# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 CERN.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Test expand referenced records Service layer RecordItem."""

from mock_module.api import Record

from invenio_records_resources.services.records.results import ExpandableField

MOCK_USER = {"id": 3, "profile": {"full_name": "John Doe"}}
MOCK_SIMPLE = {
    "id": "abcde",
    "metadata": {
        "simple_field": "simple value",
    },
}
MOCK_NESTED = {
    "id": "id_test",
    "metadata": {"nested_name": "test", "nested_field": "foo bar"},
}


class MockedService:
    def __init__(self, return_value):
        self.return_value = return_value

    def read_many(self, identity, ids):
        return type(
            "obj",
            (object,),
            {"hits": [self.return_value]},
        )


mocked_user_service = MockedService(MOCK_USER)
mocked_simple_service = MockedService(MOCK_SIMPLE)
mocked_other_service = MockedService(MOCK_NESTED)


class CreatedByExpandableField(ExpandableField):
    def get_value_service(self, value):
        """Override default."""
        if isinstance(value, dict) and value.get("user"):
            return value["user"], mocked_user_service

    def pick(self, resolved_rec):
        """Override default."""
        return {
            "id": resolved_rec["id"],
            "full_name": resolved_rec["profile"]["full_name"],
        }


class SimpleExpandableField(ExpandableField):
    def get_value_service(self, value):
        """Override default."""
        return value, mocked_simple_service

    def pick(self, resolved_rec):
        """Override default."""
        metadata = resolved_rec["metadata"]
        return {
            "id": resolved_rec["id"],
            "simple": metadata["simple_field"],
        }


class OtherExpandableField(ExpandableField):
    def get_value_service(self, value):
        """Override default."""
        return value, mocked_other_service

    def pick(self, resolved_rec):
        """Override default."""
        metadata = resolved_rec["metadata"]
        return {
            "id": resolved_rec["id"],
            "name": metadata["nested_name"],
            "nested": metadata["nested_field"],
        }


def test_result_item_fields_expansion(app, db, service, identity_simple):

    input_data = {
        "metadata": {
            "title": "Test",
            "referenced_created_by": {"user": 3},
            "referenced_simple": "abcde",
            "referenced_simple_same": "abcde",  # test 2 times the same value
            "referenced_other": {
                "nested": {"sub": "id_test"},
            },
        },
    }

    # create one record
    item = service.create(identity_simple, input_data)
    id_ = item.id

    Record.index.refresh()

    result = service.read(identity_simple, id_)
    d = result.to_dict()
    assert "expanded" not in d

    # recreate result item with the extra fields params
    # this is to avoid to mock the service and other dependencies
    result_item = service.config.result_item_cls(
        service=result._service,
        identity=result._identity,
        record=result._record,
        links_tpl=result._links_tpl,
        expandable_fields=[
            CreatedByExpandableField("metadata.referenced_created_by"),
            SimpleExpandableField("metadata.referenced_simple"),
            SimpleExpandableField("metadata.referenced_simple_same"),
            OtherExpandableField("metadata.referenced_other.nested.sub"),
        ],
        expand=True,
    )

    results = service.search(identity_simple)
    hits = results.to_dict()["hits"]["hits"]
    for hit in hits:
        assert "expanded" not in hit

    # recreate result item with the extra fields params
    result_list = service.config.result_list_cls(
        service=results._service,
        identity=results._identity,
        results=results._results,
        params=results._params,
        links_tpl=results._links_tpl,
        links_item_tpl=results._links_item_tpl,
        expandable_fields=[
            CreatedByExpandableField("metadata.referenced_created_by"),
            SimpleExpandableField("metadata.referenced_simple"),
            SimpleExpandableField("metadata.referenced_simple_same"),
            OtherExpandableField("metadata.referenced_other.nested.sub"),
        ],
        expand=True,
    )

    result = result_item.to_dict()
    assert "expanded" in result
    assert result["expanded"] == {
        "metadata": {
            "referenced_created_by": {
                "id": 3,
                "full_name": "John Doe",
            },
            "referenced_simple": {
                "id": "abcde",
                "simple": "simple value",
            },
            "referenced_simple_same": {
                "id": "abcde",
                "simple": "simple value",
            },
            "referenced_other": {
                "nested": {
                    "sub": {
                        "id": "id_test",
                        "name": "test",
                        "nested": "foo bar",
                    }
                }
            },
        }
    }

    hits = result_list.to_dict()["hits"]["hits"]
    for hit in hits:
        assert "expanded" in hit
        assert hit["expanded"] == {
            "metadata": {
                "referenced_created_by": {
                    "id": 3,
                    "full_name": "John Doe",
                },
                "referenced_simple": {
                    "id": "abcde",
                    "simple": "simple value",
                },
                "referenced_simple_same": {
                    "id": "abcde",
                    "simple": "simple value",
                },
                "referenced_other": {
                    "nested": {
                        "sub": {
                            "id": "id_test",
                            "name": "test",
                            "nested": "foo bar",
                        }
                    }
                },
            }
        }
