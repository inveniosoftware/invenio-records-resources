# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
# Copyright (C) 2020 Northwestern University.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

import json
from xml.etree import ElementTree as ET

import pytest

from invenio_records_resources.resources import RecordResource, \
    RecordResourceConfig
from invenio_records_resources.responses import RecordResponse
from invenio_records_resources.schemas import RecordSchemaJSONV1
from invenio_records_resources.serializers import RecordJSONSerializer, \
    RecordXMLSerializer
from invenio_records_resources.service import RecordService

HEADERS = {"content-type": "application/json", "accept": "application/json"}


class CustomRecordResourceConfig(RecordResourceConfig):
    """Custom record resource config."""

    item_route = "/serialization_test/records/<pid_value>"
    list_route = "/serialization_test/records"
    response_handlers = {
        "application/json": RecordResponse(
            RecordJSONSerializer(schema=RecordSchemaJSONV1)
        ),
        "application/xml": RecordResponse(RecordXMLSerializer())
    }


@pytest.fixture(scope="module")
def app(app):
    """Application factory fixture."""
    custom_bp = RecordResource(
        config=CustomRecordResourceConfig,
        service=RecordService()).as_blueprint("custom_resource")
    app.register_blueprint(custom_bp)
    yield app


def test_create_read_xml_record(client, input_record):
    # Create new record
    response = client.post(
        "/serialization_test/records", headers=HEADERS,
        data=json.dumps(input_record)
    )
    assert response.status_code == 200

    # Save record pid for posterior operations
    recid = response.json["pid"]

    # Read the XML record
    response = client.get(
        "/serialization_test/records/{}".format(recid),
        headers={
            "content-type": "application/json", "accept": "application/xml"
        }
    )
    assert response.status_code == 200
    xml_record = ET.fromstring(response.data)
    fields_to_check = [
        'pid', 'metadata', 'revision', 'created', 'updated', 'links'
    ]
    children_tags = [c.tag for c in xml_record]
    for field in fields_to_check:
        assert field in children_tags
