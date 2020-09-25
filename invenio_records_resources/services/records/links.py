# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Link schemas for records."""

from collections import OrderedDict
from copy import deepcopy

from marshmallow import Schema, fields, missing
from marshmallow_utils.fields import GenFunction, LinksField
from marshmallow_utils.links import LinksSchema
from marshmallow_utils.permissions import FieldPermissionsMixin


#
# Serializer functions
#
def pid_value_dict(record, context):
    """PID value dictionary serializer."""
    return {'pid_value': record.pid.pid_value}


def search_link_params(page_offset):
    """Search dictionary serializer."""
    def _inner(params, ctx):
        p = ctx['pagination']
        if page_offset < 0 and p.prev_page is None:
            return missing
        elif page_offset > 0 and p.next_page is None:
            return missing
        else:
            # Filter out internal parameters
            params = {
                k: v for (k, v) in params.items() if not k.startswith('_')
            }
            params['page'] += page_offset
            return {'params': params}
    return _inner


class RecordLinks(Schema, FieldPermissionsMixin):
    """Links schema."""

    field_dump_permissions = {
        'self': 'read',
    }

    self = GenFunction(pid_value_dict)


class SearchLinks(LinksSchema, FieldPermissionsMixin):
    """Search links schema."""

    namespace = 'search'

    field_dump_permissions = {
        'prev': 'search',
        'self': 'search',
        'next': 'search',
    }

    prev = GenFunction(search_link_params(-1))
    self = GenFunction(search_link_params(0))
    next = GenFunction(search_link_params(1))
