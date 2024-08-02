# -*- coding: utf-8 -*-
#
# Copyright (C) 2020-2024 CERN.
# Copyright (C) 2020 Northwestern University.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Service create update many tests."""

import pytest
from invenio_access.permissions import system_identity
from invenio_pidstore.errors import PIDDoesNotExistError

from invenio_records_resources.services.errors import PermissionDeniedError


def test_create_missing_permissions(app, service, identity_simple, input_data):
    """Create a record without permissions."""
    data = [(None, input_data)]
    with pytest.raises(PermissionDeniedError):
        service.create_or_update_many(identity_simple, data)


def test_create(app, service, input_data):
    """Create a record ."""
    data = [(None, input_data)]
    result_list = service.create_or_update_many(system_identity, data)
    result_iterator = result_list.results

    result = next(result_iterator, None)
    assert result is not None and next(result_iterator, None) is None
    record, op_type, errors = result.record, result.op_type, result.errors

    assert record.id
    assert errors == []
    assert op_type == "create"
    assert record.get("metadata") == input_data["metadata"]

    # Assert it's saved
    read_item = service.read(system_identity, record.get("id"))
    assert record.get("id") == read_item.id
    assert record.get("metadata") == read_item.data.get("metadata")


def test_create_multiple_records(app, service, input_data):
    """Create multiple records."""
    data = [(None, input_data), (None, input_data)]
    result_list = service.create_or_update_many(system_identity, data)
    results = list(result_list.results)
    assert len(results) == 2
    for record, op_type, errors in (
        (result.record, result.op_type, result.errors) for result in results
    ):
        assert record.id
        assert errors == []
        assert op_type == "create"
        assert record.get("metadata") == input_data["metadata"]

        # Assert it's saved
        read_item = service.read(system_identity, record.get("id"))
        assert record.get("id") == read_item.id
        assert record.get("metadata") == read_item.data.get("metadata")


def test_update_example_record(app, service, input_data):
    """Update an existing record."""
    item = service.create(system_identity, input_data)
    id_ = item.id
    updated_data = input_data.copy()
    updated_data["metadata"]["title"] = "Updated Title"

    data = [(id_, updated_data)]
    result_list = service.create_or_update_many(system_identity, data)
    result_iterator = result_list.results
    result = next(result_iterator, None)
    assert result is not None and next(result_iterator, None) is None

    record, op_type, errors = result.record, result.op_type, result.errors
    assert record.get("id") == id_
    assert errors == []
    assert op_type == "update"
    assert record.get("metadata")["title"] == "Updated Title"


def test_create_and_update_mixed(app, service, input_data):
    """Create and update records in one call."""
    item = service.create(system_identity, input_data)
    id_ = item.id
    updated_data = input_data.copy()
    updated_data["metadata"]["title"] = "Updated Title"

    data = [(id_, updated_data), (None, input_data)]
    result_list = service.create_or_update_many(system_identity, data)
    results = list(result_list.results)
    assert len(results) == 2
    for record, op_type, errors in (
        (result.record, result.op_type, result.errors) for result in results
    ):
        assert record.id
        assert errors == []
        if op_type == "create":
            assert record.get("metadata") == input_data["metadata"]
        elif op_type == "update":
            assert record.get("metadata")["title"] == "Updated Title"

        # Assert it's saved
        read_item = service.read(system_identity, record.get("id"))
        assert record.get("id") == read_item.id
        assert record.get("metadata") == read_item.data.get("metadata")


def test_create_with_validation_errors(app, service, invalid_input_data):
    """Create a record with validation errors."""
    data = [(None, invalid_input_data)]
    result_list = service.create_or_update_many(system_identity, data)
    result_iterator = result_list.results
    result = next(result_iterator, None)
    assert result is not None and next(result_iterator, None) is None

    record, op_type, errors = result.record, result.op_type, result.errors
    assert errors != []
    assert op_type == "create"

    # Assert it's not saved
    with pytest.raises(PIDDoesNotExistError):
        service.read(system_identity, record.get("id"))


def test_update_with_validation_errors(app, service, input_data, invalid_input_data):
    """Update an existing record with validation errors."""
    item = service.create(system_identity, input_data)
    id_ = item.id
    invalid_input_data["id"] = id_
    data = [(id_, invalid_input_data)]
    result_list = service.create_or_update_many(system_identity, data)
    result_iterator = result_list.results
    result = next(result_iterator, None)
    assert result is not None and next(result_iterator, None) is None

    record, op_type, errors = result.record, result.op_type, result.errors
    assert record.get("id") == id_
    assert errors != []
    assert op_type == "update"


def test_multiple_records(app, service, input_data, invalid_input_data):
    """Create multiple records."""
    data = [(None, input_data), (None, invalid_input_data)]
    result_list = service.create_or_update_many(system_identity, data)
    results = list(result_list.results)
    assert len(results) == 2
    for record, errors in ((result.record, result.errors) for result in results):
        if errors:
            # Assert it failed to insert
            with pytest.raises(PIDDoesNotExistError):
                service.read(system_identity, record.get("id"))
        else:
            # Assert it's saved
            read_item = service.read(system_identity, record.get("id"))
            assert record.get("id") == read_item.id
            assert record.get("metadata") == read_item.data.get("metadata")
