# SPDX-FileCopyrightText: 2020 CERN.
# SPDX-FileCopyrightText: 2020 Northwestern University.
# SPDX-License-Identifier: MIT

"""Example resource."""

from invenio_records_resources.resources import FileResourceConfig, RecordResourceConfig


class CustomRecordResourceConfig(RecordResourceConfig):
    """Custom record resource configuration."""

    blueprint_name = "mocks"
    url_prefix = "/mocks"


class CustomFileResourceConfig(FileResourceConfig):
    """Custom file resource configuration."""

    blueprint_name = "mocks_files"
    url_prefix = "/mocks/<pid_value>"


class CustomDisabledUploadFileResourceConfig(FileResourceConfig):
    """Custom file resource configuration."""

    allow_upload = False
    blueprint_name = "mocks_disabled_files_upload"
    url_prefix = "/mocks_disabled_files_upload/<pid_value>"
