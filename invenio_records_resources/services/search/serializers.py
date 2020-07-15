# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Invenio Resources module to create REST APIs."""

from dateutil import parser


def es_to_record(record_hit, record_cls):
    """Transforms an Elasticsearch record hit into a Record."""
    _id = record_hit["_id"]
    metadata = record_hit["_source"]
    revision_id = record_hit["_version"]
    # TODO: Py <3.7 cannot handle : in the offset.
    # Cannot use %Y-%m-%dT%H:%M:%S.%f%z
    updated = parser.parse(metadata["_updated"])
    created = parser.parse(metadata["_created"])

    # TODO: Potential place to remove other ES related keys
    del metadata["_updated"]
    del metadata["_created"]

    # Transform into a record
    record = record_cls(metadata)
    record.model = record.model_cls(
        id=_id,
        json=metadata,
        updated=updated,
        created=created,
        version_id=revision_id,
    )

    return record
