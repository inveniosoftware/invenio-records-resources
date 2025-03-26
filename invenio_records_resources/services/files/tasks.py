# -*- coding: utf-8 -*-
#
# Copyright (C) 2022-2024 CERN.
# Copyright (C) 2025 CESNET.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Files tasks."""

import hashlib
import traceback

import requests
from celery import shared_task
from flask import current_app
from invenio_access.permissions import system_identity
from invenio_db import db
from invenio_files_rest.models import FileInstance
from invenio_files_rest.proxies import current_files_rest

from ...proxies import current_service_registry
from ...services.errors import FileKeyNotFoundError
from ..errors import TransferException
from .transfer.constants import LOCAL_TRANSFER_TYPE


@shared_task(ignore_result=True)
def fetch_file(service_id, record_id, file_key):
    """Fetch file from external storage."""
    try:
        service = current_service_registry.get(service_id)
        transfer_metadata = service.get_transfer_metadata(
            system_identity, record_id, file_key
        )
        source_url = transfer_metadata["url"]
        # download file
        # verify=True for self signed certificates by default
        try:
            with requests.get(
                source_url, stream=True, allow_redirects=True
            ) as response:
                # save file
                if response.status_code != 200:
                    current_app.logger.error(
                        f"Failed to fetch file from {source_url} with status code {response.status_code}"
                    )
                    transfer_metadata["error"] = response.text
                    service.update_transfer_metadata(
                        system_identity, record_id, file_key, transfer_metadata
                    )
                    return
                service.set_file_content(
                    system_identity,
                    record_id,
                    file_key,
                    response.raw,  # has read method
                )
                transfer_metadata.pop("url")
                transfer_metadata["type"] = LOCAL_TRANSFER_TYPE
                service.update_transfer_metadata(
                    system_identity, record_id, file_key, transfer_metadata
                )
                # commit file
                service.commit_file(system_identity, record_id, file_key)
        except Exception as e:
            current_app.logger.error(e)
            transfer_metadata["error"] = str(e)
            service.update_transfer_metadata(
                system_identity, record_id, file_key, transfer_metadata
            )
            return

    except FileKeyNotFoundError as e:
        current_app.logger.error(e)

    except Exception as e:
        current_app.logger.error(e)
        traceback.print_exc()
        raise


@shared_task(ignore_result=True)
def recompute_multipart_checksum_task(file_instance_id):
    """Create checksum for a single object from multipart upload."""
    try:
        file_instance = FileInstance.query.filter_by(id=file_instance_id).one()
        checksum = file_instance.checksum
        if not checksum.startswith("multipart:"):
            return
        # multipart checksum looks like: multipart:<s3 multipart checksum>-part_size
        # s3 multipart checksum is the etag of the multipart object and looks like
        # hex(md5(<md5(part1) + md5(part2) + ...>))-<number of parts>
        original_checksum_hex, _number_of_parts_str, part_size_str = checksum[
            10:
        ].rsplit("-")
        part_size = int(part_size_str)

        storage = current_files_rest.storage_factory(fileinstance=file_instance)
        with storage.open("rb") as f:
            object_checksum = hashlib.md5()
            part_checksums = []
            while part_checksum := compute_checksum(f, object_checksum, part_size):
                part_checksums.append(part_checksum)
            piecewise_checksum = hashlib.md5(b"".join(part_checksums)).hexdigest()

            if piecewise_checksum != original_checksum_hex:
                raise TransferException(
                    f"Checksums do not match - recorded checksum: {original_checksum_hex}, "
                    f"computed checksum: {piecewise_checksum}"
                )

            file_instance.checksum = "md5:" + object_checksum.hexdigest()
            db.session.add(file_instance)
            db.session.commit()

    except FileKeyNotFoundError as e:
        current_app.logger.error(e)
        return
    except Exception as e:
        current_app.logger.error(e)
        traceback.print_exc()
        raise


def compute_checksum(file_stream, object_checksum, part_size):
    """Compute checksum for a single object from multipart upload."""
    buffer_size = min(1024 * 1024, part_size)
    bytes_remaining = part_size
    part_checksum = hashlib.md5()
    while bytes_remaining > 0:
        chunk = file_stream.read(min(buffer_size, bytes_remaining))
        if not chunk:
            break
        object_checksum.update(chunk)
        part_checksum.update(chunk)
        bytes_remaining -= len(chunk)
    if bytes_remaining == part_size:
        # nothing was read
        return None
    return part_checksum.digest()
