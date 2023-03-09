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


class PermissionDeniedError(PermissionDenied):
    """Permission denied error."""

    description = "Permission denied."


class RevisionIdMismatchError(Exception):
    """Etag check exception."""

    def __init__(self, record_revision_id, expected_revision_id):
        """Constructor."""
        self.record_revision_id = record_revision_id
        self.expected_revision_id = expected_revision_id

    @property
    def description(self):
        """Exception's description."""
        return (
            f"Revision id provided({self.expected_revision_id}) doesn't match "
            f"record's one({self.record_revision_id})"
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
        super().__init__(_("Facet {vocab} not found.").format(vocab=vocabulary_id))


class FileKeyNotFoundError(Exception):
    """Error denoting that a record doesn't have a certain file."""

    def __init__(self, recid, file_key):
        """Constructor."""
        super().__init__(
            _("Record '{recid}' has no file '{file_key}'.").format(
                recid=recid, file_key=file_key
            )
        )
        self.recid = recid
        self.file_key = file_key
