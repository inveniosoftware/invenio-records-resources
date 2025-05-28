# -*- coding: utf-8 -*-
#
# Copyright (C) 2020-2024 CERN.
# Copyright (C) 2020 European Union.
# Copyright (C) 2025 CESNET.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""File schema."""

from datetime import timezone
from typing import Mapping

from marshmallow import RAISE, Schema, ValidationError, post_dump, pre_load
from marshmallow.fields import UUID, Boolean, Dict, Integer, Nested, Str
from marshmallow_oneofschema import OneOfSchema
from marshmallow_utils.fields import GenMethod, Links, TZDateTime

from ...proxies import current_transfer_registry


class BaseTransferSchema(Schema):
    """Base transfer schema.

    This schema is used to dump transfer metadata during the transfer and when
    the transfer is finished.
    """

    type_ = Str(attribute="type", data_key="type", required=True)
    """Transfer type. Required field, the initial transfer type is filled 
    automatically by the InitFileSchema."""

    class Meta:
        """Meta."""

        unknown = RAISE


class TransferTypeSchemas(Mapping):
    """Mapping of transfer types to their schemas."""

    def __getitem__(self, transfer_type):
        """Get the schema for the given transfer type."""
        return current_transfer_registry.get_transfer_class(transfer_type).Schema

    def __iter__(self):
        """Iterate over the transfer types."""
        return iter(current_transfer_registry.get_transfer_types())

    def __len__(self):
        """Return the number of transfer types."""
        return len(current_transfer_registry.get_transfer_types())


class TransferSchema(OneOfSchema):
    """Transfer schema. A polymorphic schema that can handle different transfer types."""

    type_field = "type"
    type_field_remove = False
    type_schemas = TransferTypeSchemas()

    def get_obj_type(self, obj):
        """Returns name of the schema during dump() calls, given the object being dumped."""
        # obj is either a transfer object (if called on a single file) or a dictionary
        # if called on a list of files. The "get" here is for backward compatibility
        # if we have a file record that was created before the transfer was added
        return obj.get("type", current_transfer_registry.default_transfer_type)


class FileAccessSchema(Schema):
    """Schema for file access."""

    class Meta:
        """Meta."""

        unknown = RAISE

    hidden = Boolean()


class FileSchema(Schema):
    """Service schema for files."""

    class Meta:
        """Meta."""

        unknown = RAISE

    created = TZDateTime(timezone=timezone.utc, format="iso", dump_only=True)
    updated = TZDateTime(timezone=timezone.utc, format="iso", dump_only=True)

    mimetype = Str(dump_only=True, attribute="file.mimetype")
    version_id = UUID(attribute="file.version_id", dump_only=True)
    file_id = UUID(attribute="file.file_id", dump_only=True)
    bucket_id = UUID(attribute="file.bucket_id", dump_only=True)

    metadata = Dict()
    access = Nested(FileAccessSchema)

    links = Links()

    key = Str(required=True, dump_only=True)
    storage_class = Str(dump_only=True)
    checksum = Str(dump_only=True)
    size = Integer(dump_only=True)
    transfer = Nested(TransferSchema, dump_only=True)
    status = GenMethod("dump_status")
    transfer = Nested(TransferSchema, dump_only=True)

    def dump_status(self, obj):
        """Dump file status."""
        transfer = current_transfer_registry.get_transfer(
            file_record=obj,
            file_service=self.context.get("service"),
            record=obj.record,
        )
        return transfer.status

    @post_dump(pass_original=True)
    def dump_file_fields(self, obj, original, **kwargs):
        """Dump file fields."""
        # original is a FileRecord instance, might not have a file yet.
        # original.file is a file wrapper object
        # (invenio_records_resources.records.api.File)
        # We need to access the file attributes from the wrapped FileInstance
        # as getattr on the wrapper raises AttributeError if the attribute
        # is set to None.
        if original.file is not None and original.file.file is not None:
            obj["checksum"] = original.file.file.checksum
            obj["size"] = original.file.file.size
            obj["storage_class"] = original.file.file.storage_class
        # if the File wrapper is not yet created,  these attributes are taken from the
        # file record as they might have been set during file initialization. This has
        # been already handled by marshmallow.
        return obj


class InitFileSchemaMixin(Schema):
    """Service (component) schema mixin for file initialization.

    During file initialization, this mixin is merged with the FileSchema
    above.

    """

    class Meta:
        """Meta."""

        unknown = RAISE

    key = Str(required=True, dump_only=False)
    storage_class = Str(default="L", dump_only=False)
    checksum = Str(dump_only=False)
    size = Integer(dump_only=False)
    transfer = Nested(TransferSchema, dump_only=False)

    @pre_load
    def _fill_initial_transfer(self, data, **kwargs):
        """Fill in the default transfer type."""
        if not isinstance(data, dict):
            # should be a dictionary, otherwise there will be validation error later on
            return data

        data.setdefault("transfer", {})
        if not isinstance(data["transfer"], dict):
            raise ValidationError(
                {"transfer": "Transfer metadata must be a dictionary."}
            )
        data["transfer"].setdefault(
            "type", current_transfer_registry.default_transfer_type
        )
        return data
