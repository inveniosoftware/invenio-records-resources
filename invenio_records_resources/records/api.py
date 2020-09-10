# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
# Copyright (C) 2020 Northwestern University.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Records API."""

from invenio_records.api import Record as RecordBase
from invenio_records.dumpers import ElasticsearchDumper
from invenio_records.systemfields import SystemFieldsMixin, DictField


class Record(RecordBase, SystemFieldsMixin):
    """Base class for record APIs.

    Subclass this record, and specify as minimum the ``model_cls`` class-level
    attribute.
    """

    #: Disable signals - we use record extensions instead (more precise).
    send_signals = False

    #: Disable JSONRef replacement (due to complexity of configuration).
    enable_jsonref = False

    #: Default model class used by the record API (specify in subclass).
    model_cls = None

    #: Default dumper (which happens to also be used for indexing).
    dumper = ElasticsearchDumper()

    #: Metadata system field.
    metadata = DictField(clear_none=True, create_if_missing=True)
