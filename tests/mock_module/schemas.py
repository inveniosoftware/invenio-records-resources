# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2021 CERN.
# Copyright (C) 2021 Northwestern University.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Mock module schemas."""

from marshmallow import Schema, fields, validate

from invenio_records_resources.services.records.schema import BaseRecordSchema


class TypeSchema(Schema):
    """Nested type schema used for faceting tests."""

    type = fields.Str()
    subtype = fields.Str()


class MetadataSchema(Schema):
    """Basic metadata schema class."""

    title = fields.Str(required=True, validate=validate.Length(min=3))
    type = fields.Nested(TypeSchema)


class RecordSchema(BaseRecordSchema):
    """Test RecordSchema."""

    metadata = fields.Nested(MetadataSchema)


class FilesOptionsSchema(Schema):
    """Basic files options schema class."""

    enabled = fields.Bool(missing=True)


class RecordWithFilesSchema(RecordSchema):
    """Schema for records with files."""

    files = fields.Nested(FilesOptionsSchema, required=True)
