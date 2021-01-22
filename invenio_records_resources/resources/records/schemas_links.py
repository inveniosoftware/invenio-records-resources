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


#
# Parameter mappers
#
def item_link_params(record):
    """Params function to extract the pid_value."""
    return {'pid_value': record.pid.pid_value}


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


#
# Fields
#
class ItemLink(Link):
    """Item link defaults."""

    def __init__(self, **kwargs):
        """Initialize with default values."""
        kwargs.setdefault('params', item_link_params)
        kwargs.setdefault('permission', 'read')
        super().__init__(**kwargs)


class SearchLink(Link):
    """Search link defaults."""

    def __init__(self, page=0, params_func=search_link_params,
                 when_func=search_link_when, **kwargs):
        """Initialize with default values."""
        kwargs.setdefault('permission', 'search')
        kwargs.setdefault('params', params_func(page))
        kwargs.setdefault('when', when_func(page))
        super().__init__(**kwargs)


#
# Schemas
#
class LinksSchema(Schema):
    """Base factory for creating link schemas."""

    @classmethod
    def create(cls, links=None):
        """Create a new link schema."""
        attrs = links or {}
        return type('LinksSchema', (cls, ), attrs)


class ItemLinksSchema(LinksSchema):
    """Schema for a item links."""

    @classmethod
    def create(cls, **kwargs):
        """Create a new search schema using defaults."""
        links = kwargs.pop('links', {})
        links.setdefault('self', ItemLink(**kwargs))
        return super().create(links=links)


class SearchLinksSchema(LinksSchema):
    """Schema for a search result's links."""

    @classmethod
    def create(cls, **kwargs):
        """Create a new search schema using defaults."""
        links = kwargs.pop('links', {})
        links.setdefault('prev', SearchLink(page=-1, **kwargs))
        links.setdefault('self', SearchLink(page=0, **kwargs))
        links.setdefault('next', SearchLink(page=1, **kwargs))
        return super().create(links=links)
