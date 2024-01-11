# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 CERN.
# Copyright (C) 2024 TU Wien.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Files tasks."""

import json
import subprocess as sp

import requests
from celery import shared_task
from flask import current_app
from invenio_access.permissions import system_identity
from invenio_db import db
from invenio_files_rest.models import ObjectVersion, ObjectVersionTag

from ...proxies import current_service_registry
from ...services.errors import FileKeyNotFoundError


@shared_task(ignore_result=True)
def fetch_file(service_id, record_id, file_key):
    """Fetch file from external storage."""
    try:
        service = current_service_registry.get(service_id)
        file_record = service.read_file_metadata(system_identity, record_id, file_key)
        source_url = file_record.data["uri"]
        # download file
        # verify=True for self signed certificates by default
        with requests.get(source_url, stream=True, allow_redirects=True) as response:
            # save file
            service.set_file_content(
                system_identity,
                record_id,
                file_key,
                response.raw,  # has read method
            )
            # commit file
            service.commit_file(system_identity, record_id, file_key)

    except FileKeyNotFoundError as e:
        current_app.logger.error(e)


# TODO update siegfried signatures (`sf -update`) regularly
@shared_task(ignore_result=True)
def detect_file_type(bucket_id, file_key):
    """Detect the format of the file using siegfried."""
    # TODO maybe we should go through the Records-Resources files API instead?
    ov = ObjectVersion.get(bucket_id, file_key)
    if ov.file is None:
        return

    # TODO the original filename is lost (renamed to 'data'), but sf uses the filename
    #      for parts of its algorithm; possible solutions:
    #      * create a temporary alias (link?) to the file and pass that to sf
    #      * pipe the file's contents into sf via stdin and use the `-name` arg

    # TODO question: could we utilize siegfried's server mode?

    mimetype, pronom_id = None, None
    try:
        sf_bin = "sf"
        # TODO this may only be possible for 'local' storage?
        sf_output = sp.check_output([sf_bin, "-json", ov.file.uri], text=True)
        result = json.loads(sf_output)

        for file_info in result.get("files", []):
            # only consider results for the file in question
            if file_info.get("filename") != ov.file.uri:
                continue

            if not file_info.get("errors", None) and file_info.get("matches", []):
                for match in file_info["matches"]:
                    if match["ns"] == "pronom":
                        pronom_id = match["id"]

                        # NOTE: there may be results other than for the "pronom" ns
                        #       which may actually deliver better matches
                        #       e.g. for the `sway-vulkan` script, the sf website
                        #           (https://www.itforarchivists.com/siegfried)
                        #           reports "plain text file" and no mimetype for PRONOM
                        #           but "shell script" (and a mimetype) for the
                        #           "freedesktop.org" ns
                        if match["mime"]:
                            mimetype = match["mime"]

    except Exception as e:
        print(e)

    if mimetype is not None:
        ov.mimetype = mimetype
    if pronom_id is not None:
        ObjectVersionTag.create_or_update(ov, "PUID", pronom_id)

    db.session.commit()
