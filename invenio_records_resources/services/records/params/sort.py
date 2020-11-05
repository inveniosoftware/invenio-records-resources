# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Sort parameter interpreter API."""

from marshmallow import ValidationError

from .base import ParamInterpreter


class SortParam(ParamInterpreter):
    """Evaluate the 'sort' parameter."""

    def _default_sort(self, params, options):
        if params.get('q'):
            return self.config.search_sort_default
        else:
            return self.config.search_sort_default_no_query

    def _handle_empty_query(self, params, options):
        """Handles cases of empty string not matching with sort options."""
        if params['sort'] == 'bestmatch':
            return self.config.search_sort_default_no_query
        else:
            return params['sort']

    def apply(self, identity, search, params):
        """Evaluate the sort parameter on the search."""
        options = self.config.search_sort_options

        if 'sort' not in params:
            params['sort'] = self._default_sort(params, options)

        if not params.get('q'):
            params['sort'] = self._handle_empty_query(params, options)

        sort = options.get(params['sort'])
        if sort is None:
            raise ValidationError(f"Invalid sort option '{params['sort']}'.")

        return search.sort(*sort['fields'])
