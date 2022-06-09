# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 CERN.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Query parser tests."""

import pytest
from invenio_access.permissions import system_identity

from invenio_records_resources.services.records.queryparser import (
    QueryParser,
    SearchFieldTransformer,
    SuggestQueryParser,
)


@pytest.fixture()
def parser():
    """Simple parser."""
    return QueryParser(system_identity)


def test_extra_params():
    """Test for the query parser."""
    p = QueryParser(system_identity).factory(fields=["title"])
    assert p(system_identity).parse("a").to_dict() == {
        "query_string": {"query": "a", "fields": ["title"]}
    }


@pytest.mark.parametrize(
    "query",
    [
        "(new your city) OR (big apple)",
        '"a phrase"',
        "status:active",
        'author:"John Smith"',
        "book.\\*:(quick OR brown)",
        "_exists_:title",
        "qu?ck bro*",
        "name:/joh?n(ath[oa]n)/",
        "quikc~ brwn~ foks~",
        '"fox quick"~5',
        "date:[2012-01-01 TO 2012-12-31]",
        "count:[1 TO 5]",
        "tag:{alpha TO omega}",
        "count:[10 TO *]",
        "date:{* TO 2012-01-01}",
        "count:[1 TO 5}",
        "age:>10",
        "age:>=10",
        "age:<10",
        "age:<=10",
        "age:(>=10 AND <20)",
        "age:(+>=10 +<20)",
        "quick^2 fox",
        '"john smith"^2   (foo bar)^4',
        "quick brown +fox -news",
        "((quick AND fox) OR (brown AND fox) OR fox) AND NOT news",
        "(quick OR brown) AND fox",
        "status:(active OR pending) title:(full text search)^2",
        "doi:10.1234/foo.bar",
    ],
)
def test_valid_syntax(parser, query):
    """Test for the query parser."""
    assert parser.parse(query).to_dict() == {"query_string": {"query": query}}


@pytest.mark.parametrize(
    "query",
    [
        "doi:",
        "(new your city OR (big apple)",
        '"a phrase',
        'author:"John Smith',
        "name:/joh?n(ath[oan)",
        "name:joh?n(ath[oa]n)/",
        "date:[2012-01-01 to 2012-12-31]",
        "count:[1 TO 5",
        "tag:alpha TO omega}",
        "count:[10 TO ]",
        "date:{ TO 2012-01-01}",
        '"john smith"^2   (foo bar^4',
        "((quick AND fox) OR (brown AND fox OR fox) AND NOT news",
        "(quick OR brown AND fox",
    ],
)
def test_multimatch(parser, query):
    """Invalid syntax falls back to multi match query."""
    assert parser.parse(query).to_dict() == {"multi_match": {"query": query}}


@pytest.mark.parametrize(
    "query,transformed_query,query_type",
    [
        ("title:test", "metadata.title:test", "query_string"),
        ("title:(test test)", "metadata.title:(test test)", "query_string"),
        ("title:[1 TO 5]", "metadata.title:[1 TO 5]", "query_string"),
        # Invalid field names results in multi_match
        ("description:test", "description:test", "multi_match"),
        ("metadata.title:test", "metadata.title:test", "multi_match"),
    ],
)
def test_search_field_tranformer(query, transformed_query, query_type):
    """Invalid syntax falls back to multi match query."""
    p = QueryParser(system_identity).factory(
        tree_transformer_factory=SearchFieldTransformer.factory(
            mapping={"title": "metadata.title"}
        )
    )
    assert p(system_identity).parse(query).to_dict() == {
        query_type: {"query": transformed_query}
    }
