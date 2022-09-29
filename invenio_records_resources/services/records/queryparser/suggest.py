# -*- coding: utf-8 -*-
#
# Copyright (C) 2020-2022 CERN.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Query parameter interpreter API."""

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
            autocomplete_parser_cls = AutocompleteQueryParser.factory(
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
