# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2020 CERN.
# Copyright (C) 2020 Northwestern University.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Factory tests."""
import pytest
from sqlalchemy.exc import InvalidRequestError
from uritemplate import URITemplate

from invenio_records_resources.factories.factory import RecordTypeFactory
from invenio_records_resources.services import RecordServiceConfig
from invenio_records_resources.services.records.components import \
    ServiceComponent
from invenio_records_resources.services.records.schema import RecordSchema
from invenio_records_resources.services.records.search import terms_filter


def test_model_class_create():
    grant_type = RecordTypeFactory("GrantTest", RecordSchema)

    assert grant_type.model_cls.__name__ == "GrantTestMetadata"
    assert grant_type.model_cls.__tablename__ == "granttest_metadata"

    license_type = RecordTypeFactory("License", RecordSchema)

    assert license_type.model_cls.__name__ == "LicenseMetadata"
    assert license_type.model_cls.__tablename__ == "license_metadata"


def test_record_class_create():
    rec_type = RecordTypeFactory("RecordCLS", RecordSchema)

    assert rec_type.record_cls.__name__ == "RecordCLS"
    assert rec_type.record_cls.model_cls == rec_type.model_cls

    # check schema field
    assert (
        rec_type.record_cls.schema.value
        == "https://localhost/schemas/recordclss/recordcls-v1.0.0.json"
    )


def test_gen_same_name_classes():
    rec_type = RecordTypeFactory("MyRecord", RecordSchema)
    with pytest.raises(InvalidRequestError):
        rec_type2 = RecordTypeFactory("MyRecord", RecordSchema)


def test_resource_class_create():
    rec_type = RecordTypeFactory("ResourceTest", RecordSchema)

    assert rec_type.resource_cls
    assert rec_type.resource_config_cls

    assert rec_type.resource_cls.__name__ == "ResourceTestResource"
    assert (
        rec_type.resource_config_cls.__name__ == "ResourceTestResourceConfig"
    )

    assert rec_type.resource_config_cls.list_route == "/resourcetests"
    assert (
        rec_type.resource_config_cls.item_route
        == "/resourcetests/<pid_value>"
    )

    # links_schema_class = rec_type.resource_config_cls.links_config["record"]
    # search_links_schema_class = rec_type.resource_config_cls.links_config[
    #     "search"
    # ]

    # assert links_schema_class.__name__ == "ResourceTestLinksSchema"
    # assert (
    #     search_links_schema_class.__name__ == "ResourceTestSearchLinksSchema"
    # )

    # assert hasattr(links_schema_class, "self")
    # assert hasattr(search_links_schema_class, "self")
    # assert hasattr(search_links_schema_class, "prev")
    # assert hasattr(search_links_schema_class, "next")

    # assert (
    #     links_schema_class.self.template.uri
    #     == URITemplate("/api/resourcetests/{pid_value}").uri
    # )
    # assert (
    #     search_links_schema_class.self.template.uri
    #     == URITemplate("/api/resourcetests/{?params*}").uri
    # )

    # assert rec_type.resource_cls.default_config \
    # == rec_type.resource_config_cls


def test_service_class_create():
    rec_type = RecordTypeFactory("ServiceTest", RecordSchema)

    assert rec_type.service_cls
    assert rec_type.service_config_cls
    assert rec_type.service_config_cls.permission_policy_cls
    assert rec_type.service_config_cls.record_cls
    assert rec_type.service_config_cls.schema

    assert rec_type.service_cls.__name__ == "ServiceTestService"
    assert rec_type.service_config_cls.__name__ == "ServiceTestServiceConfig"

    assert rec_type.service_config_cls.schema == RecordSchema
    assert rec_type.service_config_cls.record_cls == rec_type.record_cls

    assert not rec_type.service_config_cls.search_facets_options


def test_optional_schema_path():
    rec_type = RecordTypeFactory(
        "OptionalSchemaPath",
        RecordSchema,
        schema_path="https://localhost/schemas/path/custom-v1.0.0.json",
    )

    assert (
        rec_type.record_cls.schema.value
        == "https://localhost/schemas/path/custom-v1.0.0.json"
    )


def test_optional_version():
    rec_type = RecordTypeFactory(
        "OptionalVersion", RecordSchema, schema_version="1.1.0"
    )
    assert (
        rec_type.record_cls.schema.value
        == "https://localhost/schemas/optionalversions"
        "/optionalversion-v1.1.0.json"
    )
    assert (
        rec_type.record_cls.index._name
        == "optionalversions-optionalversion-v1.1.0"
    )


def test_optional_index_name():
    rec_type = RecordTypeFactory(
        "OptionalIndex", RecordSchema, index_name="myindices-index-v1.0.0"
    )

    assert rec_type.record_cls.index._name == "myindices-index-v1.0.0"


def test_optional_endpoint_route():
    rec_type = RecordTypeFactory(
        "OptionalEndpoint", RecordSchema, endpoint_route="api/customroute"
    )

    assert rec_type.resource_config_cls.list_route == "api/customroute"
    assert (
        rec_type.resource_config_cls.item_route
        == "api/customroute/<pid_value>"
    )


def test_optional_service_params():
    search_facets_options = {
        "aggs": {
            "vocabulary_type": {
                "terms": {"field": "vocabulary_type"},
            }
        },
        "post_filters": {
            "vocabulary_type": terms_filter("vocabulary_type"),
        },
    }

    class CustomComponent(ServiceComponent):
        """Service component for metadata."""

        def create(self, identity, data=None, record=None, **kwargs):
            """Inject vocabulary type to the record."""
            record.custom_val = data.get("custom_val", None)

    rec_type = RecordTypeFactory(
        "SearchFacets",
        RecordSchema,
        search_facets_options=search_facets_options,
        service_components=[CustomComponent],
    )

    assert (
        rec_type.service_config_cls.search_facets_options
        == search_facets_options
    )

    assert (
        rec_type.service_config_cls.components
        == RecordServiceConfig.components + [CustomComponent]
    )
