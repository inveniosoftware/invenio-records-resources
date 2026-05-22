# SPDX-FileCopyrightText: 2021 CERN.
# SPDX-FileCopyrightText: 2021 Northwestern University.
# SPDX-License-Identifier: MIT

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
