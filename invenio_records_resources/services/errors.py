# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
# Copyright (C) 2020 Northwestern University.
# Copyright (C) 2023 Graz University of Technology.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Errors."""

from flask_principal import PermissionDenied
from invenio_i18n import gettext as _
from marshmallow import ValidationError


class RecordPermissionDeniedError(PermissionDenied):
    """Record permission denied error."""

    description = "Permission denied."

    def __init__(self, action_name=None, record=None, *args, **kwargs):
        """Initialize exception."""
        self.record = record
        self.action_name = action_name
        super(RecordPermissionDeniedError, self).__init__(*args, **kwargs)


class PermissionDeniedError(PermissionDenied):
    """Permission denied error."""

    @property
    def description(self):
        """Description."""
        return _("Permission denied.")


class RevisionIdMismatchError(Exception):
    """Etag check exception."""

    def __init__(self, record_revision_id, expected_revision_id):
        """Constructor."""
        self.record_revision_id = record_revision_id
        self.expected_revision_id = expected_revision_id

    @property
    def description(self):
        """Exception's description."""
        return _(
            "Revision id provided(%(expected_revision_id)s) doesn't match record's one(%(record_revision_id)s)",
            expected_revision_id=self.expected_revision_id,
            record_revision_id=self.record_revision_id,
        )


class QuerystringValidationError(ValidationError):
    """Error thrown when there is an issue with the querystring."""

    pass


class TransferException(Exception):
    """File transfer exception."""


class FacetNotFoundError(Exception):
    """Facet not found exception."""

    def __init__(self, vocabulary_id):
        """Initialise error."""
        self.vocabulary_id = vocabulary_id
        super().__init__(_("Facet %(vocab)s not found.", vocab=vocabulary_id))


class FileKeyNotFoundError(Exception):
    """Error denoting that a record doesn't have a certain file."""

    def __init__(self, recid, file_key):
        """Constructor."""
        super().__init__(
            _(
                "Record '%(recid)s' has no file '%(file_key)s'.",
                recid=recid,
                file_key=file_key,
            )
        )
        self.recid = recid
        self.file_key = file_key


class FailedFileUploadException(Exception):
    """File failed to upload exception."""

    def __init__(self, recid, file, file_key):
        """Constructor."""
        super().__init__(
            _(
                "Record '%(recid)s' failed to upload file '%(file_key)s'.",
                recid=recid,
                file_key=file_key,
            )
        )
        self.recid = recid
        self.file_key = file_key
        self.file = file


class FilesCountExceededException(Exception):
    """Files count is exceeding the max allowed exception."""

    def __init__(self, max_files, resulting_files_count):
        """Constructor."""
        super().__init__(
            _(
                "Uploading the selected files would result in {files_count} files (max is {max_files}).".format(
                    max_files=max_files, files_count=resulting_files_count
                )
            )
        )
