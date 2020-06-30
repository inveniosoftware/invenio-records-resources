# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
#
# Invenio-Resources is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Invenio Resources module to create REST APIs."""

import json

import pytz
from flask_resources.serializers import SerializerMixin


class RecordJSONSerializer(SerializerMixin):
    """Record JSON serializer implementation."""

    def __init__(self, schema=None):
        """Constructor."""
        self.schema = schema

    def _process_record(self, pid, record, response_ctx, *args, **kwargs):
        record_dict = dict(
            pid=pid,
            metadata=record.dumps(),
            revision=record.revision_id,
            created=(
                pytz.utc.localize(record.created).isoformat()
                if record.created and not record.created.tzinfo
                else None
            ),
            updated=(
                pytz.utc.localize(record.updated).isoformat()
                if record.updated and not record.updated.tzinfo
                else None
            ),
        )

        return record_dict

    def serialize_object(self, obj, response_ctx=None, *args, **kwargs):
        """Dump the object into a json string."""
        return json.dumps(
            self._process_record(obj.id, obj.record, response_ctx)
        )

    def serialize_object_list(
        self, obj_list, response_ctx=None, *args, **kwargs
    ):
        """Dump the object list into a json string."""
        records_list = [
            self._process_record(record.id, record.record, response_ctx)
            for record in obj_list
        ]

        return json.dumps(records_list)
