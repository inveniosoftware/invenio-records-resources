# -*- coding: utf-8 -*-
#
# Copyright (C) 2022-2024 CERN.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Query parser tests."""

import pytest
from flask_principal import ActionNeed
from invenio_access.permissions import Permission, SystemRoleNeed, system_identity
from luqum.tree import Phrase, Word

from invenio_records_resources.services.records.queryparser import (
    FieldValueMapper,
    QueryParser,
    SearchFieldTransformer,
)
from invenio_records_resources.services.records.queryparser.transformer import (
    RestrictedTerm,
    RestrictedTermValue,
)


@pytest.fixture()
def parser():
    """Simple parser."""
    return QueryParser(system_identity)


def test_extra_params():
    """Test for the query parser."""
    p = QueryParser.factory(fields=["title"])
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
def test_multimatch_fallback(parser, query):
    """Invalid syntax falls back to multi match query."""
    assert parser.parse(query).to_dict() == {"multi_match": {"query": query}}


@pytest.mark.parametrize(
    "query,transformed_query, allow_list",
    [
        ("title:test", "metadata.title:test", None),
        ("title:(test test)", "metadata.title:(test test)", None),
        ("title:[1 TO 5]", "metadata.title:[1 TO 5]", None),
        # term is implicitly allowed and not mapped
        # results in a query string with the original query
        ("description:test", "description:test", None),
        ("metadata.title:test", "metadata.title:test", None),
        # term is explicitly allowed and not mapped
        # results in a query string with the original query
        ("description:test", "description:test", ["description"]),
    ],
)
def test_querystring_parsing(query, transformed_query, allow_list):
    """Invalid syntax falls back to multi match query."""
    p = QueryParser.factory(
        mapping={"title": "metadata.title"},
        allow_list=allow_list,
        tree_transformer_cls=SearchFieldTransformer,
    )
    assert p(system_identity).parse(query).to_dict() == {
        "query_string": {"query": transformed_query}
    }


def test_parser_allowed_list():
    """Test the allowed list is calculated correctly."""
    p = QueryParser.factory(
        mapping={"title": "metadata.title"},
        allow_list=["description"],
        tree_transformer_cls=SearchFieldTransformer,
    )

    assert p(system_identity).allow_list == {"metadata.title", "description"}


@pytest.mark.parametrize(
    "allow_list, fields, expected_fields",
    [
        (None, None, {}),
        (None, ["description"], {"description"}),
        (["description"], None, {"description", "metadata.title"}),
        (["description"], ["description^2"], {"description^2", "metadata.title"}),
    ],
)
def test_parser_fields(allow_list, fields, expected_fields):
    """Test if the list of fields to query is calculated properly."""
    p = QueryParser.factory(
        mapping={"title": "metadata.title"},
        allow_list=allow_list,
        fields=fields,
        tree_transformer_cls=SearchFieldTransformer,
    )

    assert not set(p(system_identity).fields).difference(expected_fields)


@pytest.mark.parametrize(
    "query,transformed_query",
    [
        ("doi:10.5281/zenodo.123", 'metadata.doi:"10.5281/zenodo.123"'),
        ("doi:(blr OR biosyslit)", 'metadata.doi:("blr" OR "biosyslit")'),
        ("doi:(+blr -biosyslit) test", 'metadata.doi:(+"blr"  -"biosyslit")  test'),
        ("lol:test", "lol:lol"),
        (
            "doi:(b1 OR b2) lol:(test test1 test2)^2",
            'metadata.doi:("b1" OR "b2")  lol:(lol lol lol)^2',
        ),
    ],
)
def test_querystring_valuemapper(query, transformed_query):
    """Invalid syntax falls back to multi match query."""

    def word_to_phrase(node):
        return Phrase(
            f'"{node.value}"',
            pos=node.pos,
            size=node.size + 2,
            head=node.head,
            tail=node.tail,
        )

    def lol(node):
        node.value = "lol"
        return node

    p = QueryParser.factory(
        mapping={
            "doi": FieldValueMapper("metadata.doi", word=word_to_phrase),
            "lol": FieldValueMapper("lol", word=lol),
        },
        tree_transformer_cls=SearchFieldTransformer,
    )
    assert p(system_identity).parse(query).to_dict() == {
        "query_string": {"query": transformed_query}
    }


@pytest.mark.parametrize(
    "query,transformed_query",
    [
        # notice the input and the output of the test is the same.
        # Search field transformer does not rewrite the search query, but raises exception handled in:
        # https://github.com/inveniosoftware/invenio-records-resources/blob/e297181296eef56bdfb0d1486c3e570fa741a0aa/invenio_records_resources/services/records/queryparser/query.py#L136
        # but multimatch  will not pick up any results, due to default fields we are allowed to search on
        # integration test for this behaviour is in invenio-rdm-records
        ("internal_notes.note:abc", "internal_notes.note:abc"),
    ],
)
def test_querystring_restricted_term(query, transformed_query, identity_simple, app):
    """Invalid syntax falls back to multi match query."""

    sysadmin_permission = Permission(SystemRoleNeed("system_process"))

    def word_internal_notes(node):
        """Rewrite internal notes value."""
        if not node.value.startswith("internal_notes"):
            return node
        return Word("")

    p = QueryParser.factory(
        mapping={
            "internal_notes.note": RestrictedTerm(sysadmin_permission),
            "_exists_": RestrictedTermValue(
                sysadmin_permission, word=word_internal_notes
            ),
        },
        tree_transformer_cls=SearchFieldTransformer,
    )

    parser = p(system_identity)

    assert parser.parse(query).to_dict() == {"query_string": {"query": query}}

    parser = p(identity_simple)

    assert parser.parse(query).to_dict() == {
        "multi_match": {"query": transformed_query}
    }


@pytest.mark.parametrize(
    "query,transformed_query",
    [
        ("_exists_:internal_notes", "_exists_:"),
        ("_exists_:metadata", "_exists_:metadata"),
    ],
)
def test_querystring_restricted_term(query, transformed_query, identity_simple, app):
    """Invalid syntax falls back to multi match query."""

    sysadmin_permission = Permission(SystemRoleNeed("system_process"))

    def word_internal_notes(node):
        """Rewrite internal notes value."""
        if not node.value.startswith("internal_notes"):
            return node
        return Word("")

    p = QueryParser.factory(
        mapping={
            "internal_notes.note": RestrictedTerm(sysadmin_permission),
            "_exists_": RestrictedTermValue(
                sysadmin_permission, word=word_internal_notes
            ),
        },
        tree_transformer_cls=SearchFieldTransformer,
    )

    parser = p(system_identity)

    assert parser.parse(query).to_dict() == {"query_string": {"query": query}}

    parser = p(identity_simple)

    assert parser.parse(query).to_dict() == {
        "query_string": {"query": transformed_query}
    }
