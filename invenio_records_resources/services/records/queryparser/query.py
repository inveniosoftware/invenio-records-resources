# -*- coding: utf-8 -*-
#
# Copyright (C) 2020-2022 CERN.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Lucene query syntax parser."""

from functools import partial

from invenio_search.engine import dsl
from luqum.exceptions import ParseError
from luqum.parser import parser as luqum_parser

from invenio_records_resources.services.errors import QuerystringValidationError


class QueryParser:
    """Parse a query string into a search engine DSL Q object.

    You usually set the query parser on the ``SearchOptions``::

        class SearchOptions:
            query_parser_cls = QueryParser

    You can provide extra parameters to the parser which is sent to the search
    cluster::

        class SearchOptions:
            query_parser_cls = QueryParser.factory(
                fields=["title^2", "description"]
            )

    See the search engine reference documentation for supported
    parameters. Some include:

    - ``allow_leading_wildcard``
    - ``analyze_wildcard``
    - ``analyzer``
    - ``boost``
    - ``default_operator``
    - ``fields``
    - ``fuzziness``
    - ``lenient``

    You can also perform a transformation of the abstract syntax tree. For
    instance the following ``SearchFieldTransformer`` changes search fields
    names::

        class SearchOptions:
            query_parser_cls = QueryParser.factory(
                fields=["metadata.title^2", "metadata.description"],
                tree_transformer_factory=FieldTransformer.factory(
                    mapping={
                        "title": "metadata.title",
                        "description": "metadata.description",
                    }
                )
            )
    """

    def __init__(self, identity=None, extra_params=None, tree_transformer_factory=None):
        """Initialise the parser."""
        self.identity = identity
        self.extra_params = extra_params or {}
        self.tree_transformer_factory = tree_transformer_factory

    @classmethod
    def factory(cls, tree_transformer_factory=None, **extra_params):
        """Create a new instance of the query parser."""
        return partial(
            cls,
            extra_params=extra_params,
            tree_transformer_factory=tree_transformer_factory,
        )

    def parse(self, query_str):
        """Parse the query."""
        try:
            # We parse the Lucene query syntax in Python, so we know upfront
            # if the syntax is correct before executing it in the search engine
            tree = luqum_parser.parse(query_str)

            # Perform transformation on the abstract syntax tree (AST)
            if self.tree_transformer_factory is not None:
                transformer = self.tree_transformer_factory()
                new_tree = transformer.visit(tree, context={"identity": self.identity})
                query_str = str(new_tree)
            return dsl.Q("query_string", query=query_str, **self.extra_params)
        except (ParseError, QuerystringValidationError):
            # Fallback to a multi-match query.
            return dsl.Q("multi_match", query=query_str, **self.extra_params)
