# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
# Copyright (C) 2020 Northwestern University.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Service pagination tests.

NOTE: See tests/resources/test_pagination for more comprehensive tests.
      We test service-level aspects here.
"""

import pytest
from invenio_search import current_search


#
# Fixtures
#
@pytest.fixture(scope='module')
def records(app, service, identity_simple):
    """Input data (as coming from the view layer)."""
    items = []
    for idx in range(3):
        data = {
           'metadata': {
                'title': f'00{idx}'
            },
        }
        items.append(service.create(identity_simple, data))

    service.record_cls.index.refresh()

    return items


#
# Tests
#
def test_default_pagination(service, identity_simple, records):
    result = service.search(identity_simple).to_dict()

    # NOTE: default pagination is enough to account for 3 records in 1 page
    assert 3 == len(result["hits"]["hits"])


def test_explicit_pagination(service, identity_simple, records):
    result = service.search(
        identity_simple, page=2, size=1, _max_result=3
    ).to_dict()
    assert 1 == len(result["hits"]["hits"])
