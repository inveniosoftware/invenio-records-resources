# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 CERN.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Test expand referenced records Service layer RecordItem."""

from invenio_records_resources.services.records.results import ExpandableField
from tests.mock_module.api import Record

MOCK_USER = {"id": 3, "profile": {"full_name": "John Doe"}}
MOCK_ENTITY = {"id": "ABC", "metadata": {"title": "My title"}}
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
mocked_entity_service = MockedService(MOCK_ENTITY)
mocked_simple_service = MockedService(MOCK_SIMPLE)
mocked_other_service = MockedService(MOCK_NESTED)


class CreatedByExpandableField(ExpandableField):
    def ghost_record(self, value):
        """Override default."""
        return {}

    def system_record(self):
        """Override default."""
        raise NotImplementedError()

    def get_value_service(self, value):
        """Override default."""
        if value.get("user"):
            return value["user"], mocked_user_service
        elif value.get("entity"):
            return value["entity"], mocked_entity_service

    def pick(self, identity, resolved_rec):
        """Override default."""
        if "profile" in resolved_rec:
            return {
                "id": resolved_rec["id"],
                "full_name": resolved_rec["profile"]["full_name"],
            }
        else:
            return {
                "id": resolved_rec["id"],
                "title": resolved_rec["metadata"]["title"],
            }


class SimpleExpandableField(ExpandableField):
    def ghost_record(self, value):
        """Override default."""
        return {}

    def system_record(self):
        """Override default."""
        raise NotImplementedError()

    def get_value_service(self, value):
        """Override default."""
        return value, mocked_simple_service

    def pick(self, identity, resolved_rec):
        """Override default."""
        metadata = resolved_rec["metadata"]
        return {
            "id": resolved_rec["id"],
            "simple": metadata["simple_field"],
        }


class OtherExpandableField(ExpandableField):
    def ghost_record(self, value):
        """Override default."""
        return {}

    def system_record(self):
        """Override default."""
        raise NotImplementedError()

    def get_value_service(self, value):
        """Override default."""
        return value, mocked_other_service

    def pick(self, identity, resolved_rec):
        """Override default."""
        metadata = resolved_rec["metadata"]
        return {
            "id": resolved_rec["id"],
            "name": metadata["nested_name"],
            "nested": metadata["nested_field"],
        }


def test_result_item_fields_expansion(app, db, service, identity_simple):
    input_data1 = {
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
    input_data2 = {
        "metadata": {
            "title": "Test",
            "referenced_created_by": {"entity": "ABC"},
            "referenced_simple": "abcde",
            "referenced_simple_same": "abcde",  # test 2 times the same value
            "referenced_other": {
                "nested": {"sub": "id_test"},
            },
        },
    }

    # create 2 records
    item1 = service.create(identity_simple, input_data1)
    id1 = item1.id
    item2 = service.create(identity_simple, input_data2)
    id2 = item2.id

    Record.index.refresh()

    result1 = service.read(identity_simple, id1)
    result2 = service.read(identity_simple, id2)
    d = result1.to_dict()
    assert "expanded" not in d

    # recreate result item with the extra fields params
    # this is to avoid to mock the service and other dependencies
    result_item1 = service.config.result_item_cls(
        service=result1._service,
        identity=result1._identity,
        record=result1._record,
        links_tpl=result1._links_tpl,
        expandable_fields=[
            CreatedByExpandableField("metadata.referenced_created_by"),
            SimpleExpandableField("metadata.referenced_simple"),
            SimpleExpandableField("metadata.referenced_simple_same"),
            OtherExpandableField("metadata.referenced_other.nested.sub"),
        ],
        expand=True,
    )
    result_item2 = service.config.result_item_cls(
        service=result2._service,
        identity=result2._identity,
        record=result2._record,
        links_tpl=result2._links_tpl,
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

    result1 = result_item1.to_dict()
    assert "expanded" in result1
    assert result1["expanded"] == {
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

    result2 = result_item2.to_dict()
    assert "expanded" in result2
    assert result2["expanded"] == {
        "metadata": {
            "referenced_created_by": {
                "id": "ABC",
                "title": "My title",
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
    hit1 = [hit for hit in hits if hit["id"] == str(id1)][0]
    hit2 = [hit for hit in hits if hit["id"] == str(id2)][0]

    assert "expanded" in hit1
    assert hit1["expanded"] == {
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

    assert "expanded" in hit2
    assert hit2["expanded"] == {
        "metadata": {
            "referenced_created_by": {
                "id": "ABC",
                "title": "My title",
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
