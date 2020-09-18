# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Query interpreter API."""

import copy

from marshmallow import ValidationError
from elasticsearch_dsl import Q

from .base import ParamInterpreter

class SortParam(ParamInterpreter):
    """Evaluate the 'sort' parameter."""

    def _default_sort(self, params, options):
        if 'q' in params:
            return self.config.search_sort_default
        else:
            return self.config.search_sort_default_no_query

    def apply(self, identity, search, params):
        """Evaluate the sort parameter on the search."""
        options = self.config.search_sort_options

        if 'sort' not in params:
            params['sort'] = self._default_sort(params, options)

        sort = options.get(params['sort'])
        if sort is none:
            raise ValidationError(f"Invalid sort option '{params['sort']}'.")

        return search.sort(*sort['fields'])
