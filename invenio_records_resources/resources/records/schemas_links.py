# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
# Copyright (C) 2020 Northwestern University.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Record schema."""

from marshmallow import Schema, missing
from marshmallow_utils.fields import Link
from uritemplate import URITemplate


class RecordLinksSchema(Schema):
    """Schema for a record's links."""

    # NOTE:
    #   - /api prefix is needed here because api routes are mounted on /api
    self = Link(
        template=URITemplate("/api/records/{pid_value}"),
        permission="read",
        params=lambda record: {'pid_value': record.pid.pid_value}
    )


def search_link_params(page_offset):
    """Params function factory."""
    def _inner(search_dict):
        # Filter out internal parameters
        params = {
            k: v for k, v in search_dict.items() if not k.startswith('_')
        }
        params['page'] += page_offset
        return {'params': params}
    return _inner


def search_link_when(page_offset):
    """When function factory."""
    def _inner(search_dict):
        p = search_dict['_pagination']
        if page_offset < 0 and p.prev_page is None:
            return False
        elif page_offset > 0 and p.next_page is None:
            return False
        else:
            return True

    return _inner


class SearchLinksSchema(Schema):
    """Schema for a search result's links."""

    # NOTE:
    #   - /api prefix is needed here because api routes are mounted on /api
    self = Link(
        template=URITemplate("/api/records{?params*}"),
        permission="search",
        params=search_link_params(0)
    )
    prev = Link(
        template=URITemplate("/api/records{?params*}"),
        permission="search",
        params=search_link_params(-1),
        when=search_link_when(-1)
    )
    next = Link(
        template=URITemplate("/api/records{?params*}"),
        permission="search",
        params=search_link_params(+1),
        when=search_link_when(+1)
    )
