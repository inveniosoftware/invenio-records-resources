# -*- coding: utf-8 -*-
#
# Copyright (C) 2020-2024 CERN.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Lucene query syntax parser."""

from copy import deepcopy
from functools import partial

from invenio_search.engine import dsl
from luqum.auto_head_tail import auto_head_tail
from luqum.exceptions import ParseError
from luqum.parser import parser as luqum_parser
from werkzeug.utils import cached_property

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
                tree_transformer_factory=SearchFieldTransformer.factory(
                    mapping={
                        "title": "metadata.title",
                        "description": "metadata.description",
                    }
                )
            )
    """

    def __init__(self, identity=None, extra_params=None, tree_transformer_cls=None):
        """Initialise the parser."""
        self.identity = identity
        self.tree_transformer_cls = tree_transformer_cls
        # the query parser is instantiated once per query and the extra params is a dict
        # coming from a class attribute (passed by reference). then the popped attributes
        # would disappear after one query. we need to pop to avoid passing them to the
        # actual search query.
        self.extra_params = deepcopy(extra_params) or {}
        # the pop or {} is needed due to extra_params being passed from the factory
        # it is possible that e.g. allow_list=None and then it will fail to set()
        self.mapping = self.extra_params.pop("mapping", None) or {}
        self._allow_list = self.extra_params.pop("allow_list", None)
        # fields is not removed from extra params since if given it must be
        # used in both querystring and multi match
        self._fields = self.extra_params.get("fields") or []

    @property
    def allow_list(self):
        """Calculate the allow list."""
        if self._allow_list:  # only add the mapping if there is an allow list
            # mapping should be at least a subset of the allow list
            # implicit creation of the allow list has been chosen since there are cases
            # were the mapping list has 10s or 100s of terms and we want to avoid
            # having to duplicate those on creation in the allow list
            return set(self._allow_list).union(self.mapping.values())
        return set()

    @cached_property
    def fields(self):
        """Calculate the list of fields to query.

        It adds the allowed list of fields and remove duplications.
        For example, boosted fields.
        """
        repeated = set()
        for field in self._fields:  # check duplicated fields
            field_name = field.split("^")[0]  # remove potential boosting
            if field_name in self.allow_list:
                repeated.add(field_name)

        # fields = original fields + (allow list - repeated without boosting)
        return list(set(self._fields).union(self.allow_list.difference(repeated)))

    @classmethod
    def factory(cls, tree_transformer_cls=None, **extra_params):
        """Create a new instance of the query parser."""
        return partial(
            cls,
            extra_params=extra_params,
            tree_transformer_cls=tree_transformer_cls,
        )

    def parse(self, query_str):
        """Parse the query."""
        try:
            # We parse the Lucene query syntax in Python, so we know upfront
            # if the syntax is correct before executing it in the search engine
            tree = luqum_parser.parse(query_str)
            # Perform transformation on the abstract syntax tree (AST)
            if self.tree_transformer_cls is not None:
                transformer = self.tree_transformer_cls(
                    mapping=self.mapping,
                    allow_list=self.allow_list,
                )
                new_tree = transformer.visit(tree, context={"identity": self.identity})
                new_tree = auto_head_tail(new_tree)
                query_str = str(new_tree)
            return dsl.Q("query_string", query=query_str, **self.extra_params)
        except (ParseError, QuerystringValidationError):
            # Fallback to a multi-match query.
            if self.allow_list:
                # if there is an allow list it must overwrite a potential value
                # given by the query to include it in the fields
                kwargs = {**self.extra_params, "fields": self.fields}
                return dsl.Q("multi_match", query=query_str, **kwargs)

            # if there is no allow list we pass the parameters as default, without
            # modifying the fields, or nothing if it was not passed. this is to
            # avoid passing `fields=None`
            return dsl.Q("multi_match", query=query_str, **self.extra_params)
