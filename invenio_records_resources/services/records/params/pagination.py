# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Query interpreter API."""

from elasticsearch_dsl import Q

from ....pagination import Pagination
from .base import ParamInterpreter


class PaginationParam(ParamInterpreter):
    """Pagination evaluator."""

    param_names = ['page', 'size']

    def apply(self, identity, search, params):
        """Evaluate the query str on the search."""
        p = Pagination(
            params.get('size'),
            params.get('page'),
            params.get('_max_results'),
        )

        if not p:
            return search[p.from_idx:p.to_idx]
        return search
