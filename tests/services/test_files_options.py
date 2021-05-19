# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 CERN.
# Copyright (C) 2021 Northwestern University.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Test setting files options on the record."""

import pytest
from marshmallow import ValidationError
from mock_module.config import ServiceWithFilesConfig

from invenio_records_resources.services import RecordService

from .files_utils import add_file_to_record


@pytest.fixture(scope='module')
def service(appctx):
    """Service with files instance."""
    return RecordService(ServiceWithFilesConfig)


@pytest.fixture(scope="module")
def base_app(base_app, service, file_service):
    """Application factory fixture."""
    registry = base_app.extensions['invenio-records-resources'].registry
    registry.register(service, service_id='mock-records-service')
    registry.register(file_service, service_id='mock-files-service')
    yield base_app


def test_enable_files(app, location, service, identity_simple, input_data):
    input_data["files"] = {
        "enabled": True
    }

    item = service.create(identity_simple, input_data)

    item_dict = item.to_dict()
    assert {"enabled": True} == item_dict["files"]
    assert item._record.files.enabled is True


def test_disable_files(app, location, service, identity_simple, input_data):
    input_data["files"] = {
        "enabled": False
    }

    item = service.create(identity_simple, input_data)

    item_dict = item.to_dict()
    assert {"enabled": False} == item_dict["files"]
    assert item._record.files.enabled is False


def test_disable_files_when_files_already_present_should_error(
        app, location, service, file_service, identity_simple, input_data):
    # NOTE: The reverse is not True for practical UX reasons.
    #       We don't want to precede a file upload with a record upload for
    #       every toggle of the metadata-only checkbox.
    input_data["files"] = {
        "enabled": True
    }
    item = service.create(identity_simple, input_data)
    add_file_to_record(file_service, item.id, 'file.txt', identity_simple)
    input_data["files"] = {
        "enabled": False
    }

    with pytest.raises(ValidationError):
        item = service.update(item.id, identity_simple, input_data)


def test_set_default_file_preview(
        app, location, service, file_service, identity_simple, input_data):
    input_data["files"] = {
        "enabled": True,
    }
    item = service.create(identity_simple, input_data)
    default_file = 'file.txt'
    add_file_to_record(file_service, item.id, default_file, identity_simple)
    input_data["files"] = {
        "enabled": True,
        "default_preview": default_file
    }

    item = service.update(item.id, identity_simple, input_data)

    item_dict = item.to_dict()
    assert (
        {"enabled": True, "default_preview": default_file} ==
        item_dict["files"]
    )
    assert item._record.files.default_preview == default_file


def test_set_default_file_preview_when_unknown_should_raise(
        app, location, service, file_service, identity_simple, input_data):
    input_data["files"] = {
        "enabled": True,
    }
    item = service.create(identity_simple, input_data)
    default_file = 'file.txt'
    add_file_to_record(file_service, item.id, default_file, identity_simple)
    input_data["files"] = {
        "enabled": True,
        "default_preview": "inexisting_file.txt"
    }

    with pytest.raises(ValidationError):
        item = service.update(item.id, identity_simple, input_data)
