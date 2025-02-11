# -*- coding: utf-8 -*-
#
# Copyright (C) 2020-2024 CERN.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Query parameter interpreter API."""

# Here for backward compatibility
from invenio_i18n import gettext as _

from ...errors import QuerystringValidationError
from ..queryparser import QueryParser, SuggestQueryParser  # noqa
from .base import ParamInterpreter


class QueryStrParam(ParamInterpreter):
    """Evaluate the 'q' or 'suggest' parameter."""

    def apply(self, identity, search, params):
        """Evaluate the query str on the search."""
        q_str = params.get("q")
        suggest_str = params.get("suggest")

        if q_str and suggest_str:
            raise QuerystringValidationError(
                _(
                    "You cannot specify both 'q' and 'suggest' parameters at the "
                    "same time."
                )
            )

        query_str = q_str
        parser_cls = self.config.query_parser_cls
        if suggest_str:
            query_str = suggest_str
            parser_cls = self.config.suggest_parser_cls
            if parser_cls is None:
                raise QuerystringValidationError(_("Invalid 'suggest' parameter."))

        if query_str:
            query = parser_cls(identity).parse(query_str)
            search = search.query(query)

        return search
