# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2020 CERN.
# Copyright (C) 2020 Northwestern University.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Record metaclass."""
from invenio_pidstore.providers.recordid_v2 import RecordIdProviderV2
from invenio_records import Record
from invenio_records.dumpers import ElasticsearchDumper
from invenio_records.systemfields import ConstantField
from invenio_records_resources.records.systemfields import IndexField, PIDField


class RecordMeta(type):
    name = None
    schema_version = None
    schema_path = None
    index_name = None
    bases = (Record,)

    schema_path_template = (
        "https://localhost/schemas/{name_plural}/{name}-v{version}.json"
    )
    index_name_template = "{name_plural}-{name}-v{version}"

    def __new__(
        mcs,
        name,
        attrs=None,
        schema_version="1.0.0",
        schema_path=None,
        index_name=None,
        dumper=None,
    ):
        if attrs is None:
            attrs = {}
        mcs.schema_path = schema_path
        mcs.index_name = index_name
        mcs.name = name
        mcs.schema_version = schema_version
        attrs.update(
            {
                "schema": ConstantField("$schema", mcs.generate_schema_path()),
                "index": IndexField(mcs.generate_index_name()),
                "pid": PIDField("id", provider=RecordIdProviderV2),
                "dumper": dumper if dumper else ElasticsearchDumper(),
            }
        )
        return super().__new__(mcs, name, (), attrs)

    def __init__(
        cls,
        name,
        attrs=None,
        schema_version="1.0.0",
        schema_path=None,
        index_name=None,
        dumper=None,
    ):
        super().__init__(name, cls.bases, attrs)

    @classmethod
    def name_plural(mcs):
        return "{}s".format(mcs.name).lower()

    @classmethod
    def generate_schema_path(mcs):
        if mcs.schema_path:
            return mcs.schema_path
        return mcs.schema_path_template.format(
            name_plural=mcs.name_plural(),
            name=mcs.name.lower(),
            version=mcs.schema_version,
        )

    @classmethod
    def generate_index_name(mcs):
        if mcs.index_name:
            return mcs.index_name
        return mcs.index_name_template.format(
            name_plural=mcs.name_plural(),
            name=mcs.name.lower(),
            version=mcs.schema_version,
        )
