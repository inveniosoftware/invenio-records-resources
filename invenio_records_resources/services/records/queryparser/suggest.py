# -*- coding: utf-8 -*-
#
# Copyright (C) 2020-2024 CERN.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Query parameter interpreter API."""

from functools import partial

from invenio_search.engine import dsl

from .query import QueryParser


class SuggestQueryParser(QueryParser):
    """Query parser is useful for search-as-you-type/auto completion features.

    The query parser creates a search engine multi match query with the
    default type ``bool_prefix``. It works in conjunction with having one or
    more ``search_as_you_type`` fields defined in your search engine mapping.

    First, you need to define one or more ``search_as_you_type`` fields in your
    index mapping, e.g.::

        "keywords": {
            "type": "search_as_you_type"
        },

    Next, you have you define the query parser to specifically search the
    fields::

        class MySearchOptions(SearchOptions):
            # ...
            suggest_parser_cls = SuggestQueryParser.factory(
                fields=[
                    'keywords',
                    'keywords._2gram',
                    'keywords._3gram',
                ],
            )

    The two fields ``keywords._2gram`` and ``keywords._3gram`` are created
    by the ``search_as_you_type`` field.

    For more information see:
    - https://www.elastic.co/guide/en/elasticsearch/reference/current/query-dsl-multi-match-query.html
    - https://www.elastic.co/guide/en/elasticsearch/reference/current/search-as-you-type.html
    """  # noqa

    def __init__(self, identity=None, extra_params=None, **kwargs):
        """Constructor."""
        super().__init__(identity=identity, extra_params=extra_params)
        self.extra_params.setdefault("type", "bool_prefix")

    def parse(self, query_str):
        """Parse the query."""
        return dsl.Q("multi_match", query=query_str, **self.extra_params)


class CompositeSuggestQueryParser(QueryParser):
    """Composite query parser for suggestion-style queries.

    Allows for multiple multi-match clauses to be combined in a single bool query.
    See https://www.elastic.co/guide/en/elasticsearch/reference/current/query-dsl-multi-match-query.html for more information on the various types
    of multi-match queries available, and recommendations on when/how to use each.
    """

    def __init__(self, identity=None, extra_params=None, clauses=None, **kwargs):
        """Constructor."""
        super().__init__(identity=identity, extra_params=extra_params)
        # Default operator is "and", to make sure we narrow down results
        self.extra_params.setdefault("operator", "and")
        self.clauses = clauses or [
            # "cross_fields" helps when we expect the entire query to be searched across
            # multiple fields (e.g. full name + affiliation + affiliation acronym).
            {"type": "cross_fields", "boost": 3},
            # "bool_prefix" is useful for search-as-you-type/auto completion features.
            # Ref: https://opensearch.org/docs/latest/analyzers/tokenizers/edge-n-gram/
            # It works in conjunction with having search_as_you_type fields but for custom
            # edge-ngram-analyzed fields it is not needed because the expansions already
            # exist in the index, so essentially, bool_prefix is doing the same work
            # Ref: https://opensearch.org/docs/latest/analyzers/token-filters/edge-ngram/
            # {"type": "bool_prefix", "boost": 2, "fuzziness": "AUTO"},
            # "most_fields" is here to boost results where more fields match the
            # query. E.g. the query "john doe acme" would match "name:(john doe)" and
            # "affiliation.acronym:(acme)", instead of a case where only one field
            # like "name:(john doe acme)" matches.
            # We also enable fuzziness to allow for small typos.
            {"type": "most_fields", "boost": 1, "fuzziness": "AUTO"},
        ]

    @classmethod
    def factory(cls, tree_transformer_cls=None, clauses=None, **extra_params):
        """Factory method."""
        return partial(
            cls,
            tree_transformer_cls=tree_transformer_cls,
            clauses=clauses,
            extra_params=extra_params,
        )

    def parse(self, query_str):
        """Parse and build the query."""
        should_clauses = []

        for clause in self.clauses:
            params = {**self.extra_params, **clause}

            # By default strip field boosting from cross_fields (e.g. "name^2") as it's
            # not recommended in the docs.
            strip_cross_fields_boost = params.pop("strip_cross_fields_boost", True)
            is_cross_fields = clause["type"] == "cross_fields"
            if is_cross_fields and strip_cross_fields_boost and params.get("fields"):
                params["fields"] = [f.split("^")[0] for f in params["fields"]]

            should_clauses.append(dsl.Q("multi_match", query=query_str, **params))

        return dsl.Q("bool", should=should_clauses)
