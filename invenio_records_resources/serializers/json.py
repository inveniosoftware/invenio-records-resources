# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
# Copyright (C) 2020 Northwestern University.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Invenio Resources module to create REST APIs."""

import json

import pytz
from flask_resources.serializers import SerializerMixin


class RecordJSONSerializer(SerializerMixin):
    """Record JSON serializer implementation."""

    def __init__(self, schema=None):
        """Constructor."""
        self.schema = schema

    def _process_record(self, record_state, *args, **kwargs):
        pid = record_state.id
        record = record_state.record
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
            links=record_state.links
        )

        return record_dict

    def serialize_object(self, obj, response_ctx=None, *args, **kwargs):
        """Dump the object into a json string."""
        if obj:  # e.g. delete op has no return body
            return json.dumps(self._process_record(obj))
        else:
            return ""

    def serialize_object_list(
        self, obj_list, response_ctx=None, *args, **kwargs
    ):
        """Dump the object list into a json string.

        :param: obj_list a IdentifiedRecords object
        """
        serialized_content = {
            "hits": {
                "hits": [
                    self._process_record(record, response_ctx)
                    for record in obj_list.records
                ],
                "total": obj_list.total
            },
            "links": obj_list.links,
            "aggregations": obj_list.aggregations
        }

        return json.dumps(serialized_content)
