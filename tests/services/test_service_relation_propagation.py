# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 CERN.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Service tests for record relations propagation."""

from copy import deepcopy

import pytest
from mock_module.api import Record, RecordWithRelations
from mock_module.config import ServiceConfig as ServiceConfigBase

from invenio_records_resources.proxies import (
    current_notifications_registry,
    current_service_registry,
)
from invenio_records_resources.services import RecordService
from invenio_records_resources.services.records.components import (
    ChangeNotificationsComponent,
    RelationsComponent,
)


@pytest.fixture(scope="module")
def service(appctx):
    """Service instance."""

    class ServiceConfig(ServiceConfigBase):
        """Record cls config."""

        record_cls = Record

        components = ServiceConfigBase.components + [
            ChangeNotificationsComponent,
        ]

    service = RecordService(ServiceConfig)
    current_service_registry.register(service)

    return service


@pytest.fixture(scope="module")
def service_wrel(appctx):
    """Service instance for records with relations."""

    class ServiceConfig(ServiceConfigBase):
        """Record cls config."""

        record_cls = RecordWithRelations
        relations = {"mock-records": ["metadata.inner_record"]}

        components = ServiceConfigBase.components + [RelationsComponent]

    service = RecordService(ServiceConfig)
    current_service_registry.register(service, "recordwithrelations")

    return service


def assert_record_from_db_and_es(
    identity, service, recid, id_, title=None, title_db=None, title_es=None
):
    title_db = title_db or title
    title_es = title_es or title
    # db
    from_db = service.read(identity, recid)
    assert from_db["metadata"]["inner_record"]["id"] == id_
    assert from_db["metadata"]["inner_record"]["metadata"]["title"] == title_db

    # search
    from_search = service.search(identity, {"q": recid})
    assert from_search.total == 1
    from_search = list(from_search.hits)[0]
    assert from_search["metadata"]["inner_record"]["id"] == id_
    assert from_search["metadata"]["inner_record"]["metadata"]["title"] == title_es


def test_relation_update_propagation(
    app, service, service_wrel, identity_simple, input_data
):
    # this notification handlers would be registerd at extension loading
    current_notifications_registry.register(service.id, service_wrel.on_relation_update)

    # create a record
    item = service.create(identity_simple, input_data)
    service.record_cls.index.refresh()
    id_ = item.id
    title = item["metadata"]["title"]

    # create a record with the above as relation
    wrel_data = deepcopy(input_data)
    wrel_data["metadata"]["inner_record"] = {"id": id_}
    rec_one = service_wrel.create(identity_simple, wrel_data)
    rec_two = service_wrel.create(identity_simple, wrel_data)
    service_wrel.record_cls.index.refresh()

    assert_record_from_db_and_es(identity_simple, service_wrel, rec_one.id, id_, title)
    assert_record_from_db_and_es(identity_simple, service_wrel, rec_two.id, id_, title)

    # update related record
    updated_data = deepcopy(input_data)
    updated_data["metadata"]["title"] = "new title"
    item = service.update(identity_simple, id_, updated_data)
    service.record_cls.index.refresh()

    read_item = service.read(identity_simple, id_)
    assert read_item["metadata"]["title"] == "new title"

    # call update on one of the records so it gets reindexed
    _ = service_wrel.update(identity_simple, rec_two.id, wrel_data)
    service_wrel.record_cls.index.refresh()
    assert_record_from_db_and_es(  # rec one still the same
        identity_simple,
        service_wrel,
        rec_one.id,
        id_,
        title_db="new title",  # cmp deref makes a query so it is updated
        title_es=title,  # search did not get updated yet
    )
    assert_record_from_db_and_es(
        identity_simple, service_wrel, rec_two.id, id_, "new title"
    )

    # process the index queue
    # in a prod deployment this would be run by a celery beat task
    assert service_wrel.indexer.process_bulk_queue() == (2, 0)
    service_wrel.record_cls.index.refresh()
    # read the record and check the reference got updated
    assert_record_from_db_and_es(
        identity_simple, service_wrel, rec_one.id, id_, "new title"
    )
    assert_record_from_db_and_es(
        identity_simple, service_wrel, rec_two.id, id_, "new title"
    )
