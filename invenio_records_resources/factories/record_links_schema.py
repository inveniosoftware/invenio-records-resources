# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2020 CERN.
# Copyright (C) 2020 Northwestern University.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Record Links Schema metaclass."""
from marshmallow import Schema
from marshmallow_utils.fields import Link
from uritemplate import URITemplate


class RecordLinksSchemaMeta(type):
    """Record links schema type."""

    bases = (Schema,)

    def __new__(mcs, attrs, record_type_name, endpoint_route):
        """Object creation."""
        mcs.name = f"{record_type_name}LinksSchema"

        # TODO better template building ?
        url_template = f"/api{endpoint_route}" + "/{pid_value}"

        attrs.update(
            {
                "self": Link(
                    template=URITemplate(url_template),
                    permission="read",
                    params=lambda record: {
                        "pid_value": record.pid.pid_value,
                    },
                    data_key="self",
                    # To avoid using self since is python reserved key
                )
            }
        )
        return super().__new__(mcs, mcs.name, (), attrs)

    def __init__(cls, attrs, model_name, endpoint_route):
        """Initialisation."""
        super().__init__(cls.name, cls.bases, attrs)
