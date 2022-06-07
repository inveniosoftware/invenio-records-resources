# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
# Copyright (C) 2020-2021 Northwestern University.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Service revision_id tests."""

import pytest

from invenio_records_resources.services.errors import RevisionIdMismatchError


@pytest.fixture()
def input_data(identity_simple, service):
    """Input data (as coming from the view layer)."""
    data = {"metadata": {"title": "Test"}}
    item = service.create(identity_simple, data)

    # TODO: Should this be part of the service? we don't know the index easily
    service.record_cls.index.refresh()
    return item


def test_revision_id_update(app, service, identity_simple, input_data):
    """Test revision_id check on record updates."""

    data = input_data.to_dict()
    data_revision_id = data["revision_id"]

    # Update outdated record
    with pytest.raises(RevisionIdMismatchError):
        service.update(identity_simple, input_data.id, data, revision_id=100)

    # Update with correct revision_id

    assert service.update(
        identity_simple, input_data.id, data, revision_id=data_revision_id
    )


def test_revision_id_delete(app, service, identity_simple, input_data):
    """Test revision_id check on record deletions."""

    data = input_data.to_dict()
    data_revision_id = data["revision_id"]

    # Delete outdated record
    with pytest.raises(RevisionIdMismatchError):
        service.delete(identity_simple, input_data.id, revision_id=100)

    # Delete with correct revision_id

    assert service.delete(identity_simple, input_data.id, revision_id=data_revision_id)
