# SPDX-FileCopyrightText: 2022-2024 CERN.
# SPDX-FileCopyrightText: 2025 CESNET.
# SPDX-License-Identifier: MIT

"""Files tasks."""

import hashlib
import traceback

import requests
from celery import shared_task
from flask import current_app
from invenio_access.permissions import system_identity
from invenio_db import db
from invenio_files_rest.models import FileInstance, ObjectVersion
from invenio_files_rest.proxies import current_files_rest

from ...proxies import current_service_registry
from ...services.errors import FileKeyNotFoundError
from ..errors import TransferException


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
                result = service.set_file_content(
                    system_identity,
                    record_id,
                    file_key,
                    response.raw,  # has read method
                )
                if result.errors:
                    return
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


@shared_task(
    ignore_result=True,
    acks_late=True,
    retry_backoff=True,
    max_retries=10,
    autoretry_for=(Exception,),
)
def cleanup_failed_upload(file_instance_id, uri):
    """Undo a reservation left behind by an upload that could not finish.

    Idempotent: it only touches a file instance that still holds the path the
    upload wrote, so a committed file or a re-used key is left alone.
    """
    file_instance = (
        FileInstance.query.filter_by(id=file_instance_id)
        .populate_existing()
        .with_for_update()
        .one_or_none()
    )
    if file_instance is None or file_instance.readable or file_instance.uri != uri:
        db.session.rollback()
        return

    storage = file_instance.storage()
    if ObjectVersion.query.filter_by(file_id=file_instance_id).count():
        # An object version still points at the row, and deleting it would
        # break that foreign key. Reset it so the file goes back to pending and
        # can be uploaded again. An UPDATE, because the model's uri validator
        # rejects None.
        FileInstance.query.filter_by(id=file_instance_id).update(
            {
                "uri": None,
                "size": 0,
                "checksum": None,
                "readable": False,
                "writable": True,
            },
            synchronize_session=False,
        )
    else:
        file_instance.delete()
    db.session.commit()

    try:
        storage.delete()
    except FileNotFoundError:
        # A concurrent delete already removed the file.
        pass


@shared_task(
    ignore_result=True,
    acks_late=True,
    retry_backoff=True,
    max_retries=10,
    autoretry_for=(Exception,),
)
def recompute_multipart_checksum_task(file_instance_id):
    """Create checksum for a single object from multipart upload."""
    try:
        file_instance = FileInstance.query.filter_by(id=file_instance_id).one_or_none()
        if not file_instance:
            # the file instance has been already deleted, for example user has deleted the draft
            # or removed the file from the draft
            return
        checksum = file_instance.checksum
        if not checksum:
            # multipart checksum not present -> compute normal checksum
            file_instance.update_checksum()
            db.session.add(file_instance)
            db.session.commit()
            return
        elif not checksum.startswith("multipart:"):
            # checksum has already been computed, nothing to do
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
