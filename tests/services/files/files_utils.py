# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 CERN.
# Copyright (C) 2021 Northwestern University.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Files utils for testing."""

from io import BytesIO


def add_file_to_record(file_service, recid, file_id, identity):
    """Add a file to the record."""
    file_service.init_files(identity, recid, data=[{"key": file_id}])
    file_service.set_file_content(
        identity, recid, file_id, BytesIO(b"test file content")
    )
    result = file_service.commit_file(identity, recid, file_id)
    return result
