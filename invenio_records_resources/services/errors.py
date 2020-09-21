# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
# Copyright (C) 2020 Northwestern University.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Errors."""

from flask_principal import PermissionDenied
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
