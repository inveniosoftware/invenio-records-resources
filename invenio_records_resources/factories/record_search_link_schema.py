# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2020 CERN.
# Copyright (C) 2020 Northwestern University.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Record search links schema metaclass."""
from marshmallow import Schema
from marshmallow_utils.fields import Link
from uritemplate import URITemplate

from invenio_records_resources.resources import search_link_params, \
    search_link_when


class RecordSearchLinksSchemaMeta(type):
    """Record search links schema."""

    bases = (Schema,)

    def __new__(mcs, attrs, record_type_name, endpoint_route):
        """Object creation."""
        # TODO better template building ?
        url_template = f"/api{endpoint_route}" + "/{?params*}"

        mcs.name = f"{record_type_name}SearchLinksSchema"

        attrs.update(
            {
                "self": Link(
                    template=URITemplate(url_template),
                    permission="search",
                    params=search_link_params(0),
                ),
                "prev": Link(
                    template=URITemplate(url_template),
                    permission="search",
                    params=search_link_params(-1),
                    when=search_link_when(-1),
                ),
                "next": Link(
                    template=URITemplate(url_template),
                    permission="search",
                    params=search_link_params(+1),
                    when=search_link_when(+1),
                ),
            }
        )
        return super().__new__(mcs, mcs.name, (), attrs)

    def __init__(cls, attrs, model_name, endpoint_route):
        """Initialisation."""
        super().__init__(cls.name, cls.bases, attrs)
