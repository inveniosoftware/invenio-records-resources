# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2020 CERN.
# Copyright (C) 2020 Northwestern University.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Record type factory."""
from invenio_records_permissions import RecordPermissionPolicy

from invenio_records_resources.factories.record_links_schema import (
    RecordLinksSchemaMeta,
)
from invenio_records_resources.factories.record import RecordMeta
from invenio_records_resources.factories.record_metadata import (
    RecordMetadataMeta,
)
from invenio_records_resources.factories.record_search_link_schema import (
    RecordSearchLinksSchemaMeta,
)
from invenio_records_resources.resources import (
    RecordResourceConfig,
    RecordResource,
)
from invenio_records_resources.services import (
    RecordServiceConfig,
    RecordService,
)


class RecordTypeFactory(object):
    model_cls = None
    record_cls = None
    resource_cls = None
    resource_config_cls = None
    service_config_cls = None
    service_cls = None

    def __init__(
        self,
        record_type_name,
        record_type_service_schema,
        schema_version="1.0.0",
        endpoint_route=None,
        record_dumper=None,
        schema_path=None,
        index_name=None,
        search_facets_options=None,
        service_components=None,
        permission_policy_cls=None
    ):
        self.record_type_name = record_type_name
        self.record_name_lower = record_type_name.lower()

        # record class attributes
        self.schema_version = schema_version
        self.record_dumper = record_dumper
        self.schema_path = schema_path
        self.index_name = index_name

        # resource class attributes
        self.endpoint_route = endpoint_route

        # service attributes
        self.record_type_service_schema = record_type_service_schema
        self.search_facets_options = search_facets_options
        self.service_components = service_components
        self.permission_policy_cls = permission_policy_cls

        self.validate()

        self.create_record_type()

    def validate(self):
        # TODO - specify what should be validated
        pass

    def create_record_type(self):
        # methods should call in this order, since classes have dependencies
        self.create_metadata_model()
        self.create_record_class()
        self.create_resource_class()
        self.create_service_class()

    def create_metadata_model(self):

        self.model_cls = RecordMetadataMeta(self.record_type_name)

    def create_record_class(self):
        record_class_attributes = {"model_cls": self.model_cls}
        self.record_cls = RecordMeta(
            self.record_type_name,
            attrs=record_class_attributes,
            schema_version=self.schema_version,
            dumper=self.record_dumper,
            schema_path=self.schema_path,
            index_name=self.index_name,
        )

    def _create_links_schemas_class(self, list_route):
        record_link_schema_cls = RecordLinksSchemaMeta(
            {}, self.record_type_name, list_route
        )
        record_search_link_schema_cls = RecordSearchLinksSchemaMeta(
            {}, self.record_type_name, list_route
        )

        return record_link_schema_cls, record_search_link_schema_cls

    def create_resource_class(self):
        resource_config_cls_name = f"{self.record_type_name}ResourceConfig"
        resource_cls_name = f"{self.record_type_name}Resource"

        list_route = self.endpoint_route or f"api/{self.record_name_lower}s"
        item_route = f"{list_route}/<pid_value>"

        record_link_schema_cls, record_search_link_schema_cls = \
            self._create_links_schemas_class(list_route)

        config_cls_attributes = {
            "list_route": list_route,
            "item_route": item_route,
            "links_config": {
                "record": record_link_schema_cls,
                "search": record_search_link_schema_cls,
            },
        }

        self.resource_config_cls = type(
            resource_config_cls_name,
            (RecordResourceConfig,),
            config_cls_attributes,
        )
        resource_cls_attributes = {"default_config": self.resource_config_cls}

        self.resource_cls = type(
            resource_cls_name, (RecordResource,), resource_cls_attributes
        )

    def create_service_class(self):
        permission_policy_cls_name = f"{self.record_type_name}PermissionPolicy"
        config_cls_name = f"{self.record_type_name}ServiceConfig"
        service_cls_name = f"{self.record_type_name}Service"

        # if permission policy not given, create a standard one
        if not self.permission_policy_cls:
            self.permission_policy_cls = type(
                permission_policy_cls_name, (RecordPermissionPolicy,), {}
            )

        config_cls_attributes = {
            "permission_policy_cls": self.permission_policy_cls,
            "record_cls": self.record_cls,
            "search_facets_options": self.search_facets_options,
            "schema": self.record_type_service_schema,
        }
        if self.service_components:
            config_cls_attributes.update(
                {
                    "components": RecordServiceConfig.components
                    + self.service_components
                }
            )

        self.service_config_cls = type(
            config_cls_name, (RecordServiceConfig,), config_cls_attributes
        )

        service_cls_attributes = {"default_config": self.service_config_cls}
        self.service_cls = type(
            service_cls_name, (RecordService,), service_cls_attributes
        )
