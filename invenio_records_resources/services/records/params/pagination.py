# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Pagination parameter interpreter API."""

from marshmallow import ValidationError

from ....pagination import Pagination
from ...errors import QuerystringValidationError
from .base import ParamInterpreter


class PaginationParam(ParamInterpreter):
    """Pagination evaluator."""

    def apply(self, identity, search, params):
        """Evaluate the query str on the search."""
        options = self.config.pagination_options

        default_size = options["default_results_per_page"]

        params.setdefault("size", default_size)
        params.setdefault("page", 1)

        p = Pagination(
            params["size"],
            params["page"],
            options["default_max_results"],
        )

        if not p.valid():
            raise QuerystringValidationError("Invalid pagination parameters.")

        return search[p.from_idx:p.to_idx]
