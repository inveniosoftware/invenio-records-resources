# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
# Copyright (C) 2020 Northwestern University.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Service tests."""


def test_service_read(service, example_record, identity_simple):
    """Read a record with the service."""
    recstate = service.read(identity_simple, example_record.id)
    assert recstate.id == str(example_record.id)
