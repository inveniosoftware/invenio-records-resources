# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2020 CERN.
# Copyright (C) 2020 Northwestern University.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Record Metadata metaclass."""
from invenio_db import db
from invenio_records.models import RecordMetadataBase
from invenio_records_resources.factories.validation import Registered


class RecordMetadataMeta(Registered):
    class_name = None
    tablename_template = "{name}_metadata"
    pid = db.Column(db.String)
    bases = (
        db.Model,
        RecordMetadataBase,
    )

    def __new__(mcs, name):
        mcs.class_name = "{}Metadata".format(name)

        mcs.validate_cls(mcs.class_name)

        attrs = dict(
            pid=mcs.pid,
            __tablename__=mcs.tablename_template.format(name=name.lower())
        )

        new = super().__new__(mcs, mcs.class_name, (), attrs)

        # register the class in the module to check for duplicates
        mcs.register_in_module(new)
        return new

    def __init__(cls, name, bases=(), attrs=None):
        bases = cls.bases + bases
        super().__init__(name, bases, attrs)
