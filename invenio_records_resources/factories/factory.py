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
from invenio_db import db
from invenio_pidstore.providers.recordid_v2 import RecordIdProviderV2
from invenio_records.dumpers import SearchDumper
from invenio_records.models import RecordMetadataBase
from invenio_records.systemfields import ConstantField
from invenio_records_permissions import RecordPermissionPolicy

from invenio_records_resources.records.api import Record
from invenio_records_resources.records.systemfields import IndexField, PIDField
from invenio_records_resources.records.systemfields.pid import PIDFieldContext
from invenio_records_resources.resources import RecordResource, RecordResourceConfig
from invenio_records_resources.services import RecordService, RecordServiceConfig
from invenio_records_resources.services.records.config import SearchOptions
from invenio_records_resources.services.records.links import (
    RecordLink,
    pagination_links,
)


class RecordTypeFactory(object):
    """Factory of record types."""

    model_cls = None
    record_cls = None
    resource_cls = None
    resource_config_cls = None
    service_config_cls = None
    service_cls = None

    _schema_path_template = (
        "https://localhost/schemas/{name_plural}/{name}-v{version}.json"
    )
    _index_name_template = "{name_plural}-{name}-v{version}"

    def __init__(
        self,
        record_type_name,
        service_schema,
        schema_version="1.0.0",
        endpoint_route=None,
        record_dumper=None,
        record_relations=None,
        schema_path=None,
        index_name=None,
        search_options=None,
        service_components=None,
        permission_policy_cls=None,
        pid_field_cls=PIDField,
        pid_field_kwargs=None,
        model_cls_attrs=None,
        record_cls_attrs=None,
        resource_cls_attrs=None,
        service_id=None,
    ):
        """Constructor."""
        self.record_type_name = record_type_name
        self.record_name_lower = record_type_name.lower()
        self.name_plural = f"{self.record_name_lower}s"

        # pid field attributes
        self.pid_field_cls = pid_field_cls
        self.pid_field_kwargs = pid_field_kwargs or {
            "key": "id",
            "create": True,
            "provider": RecordIdProviderV2,
            "context_cls": PIDFieldContext,
        }

        # record class attributes
        self.schema_version = schema_version
        self.record_dumper = record_dumper
        self.record_relations = record_relations
        self.schema_path = self._build_schema_path(schema_path)
        self.index_name = self._build_index_name(index_name)
        self.model_cls_attrs = model_cls_attrs or {}
        self.record_cls_attrs = record_cls_attrs or {}
        self.resource_cls_attrs = resource_cls_attrs or {}

        # resource class attributes
        self.endpoint_route = endpoint_route

        # service attributes
        self.service_id = service_id
        self.service_schema = service_schema
        self.search_options = search_options or SearchOptions
        self.service_components = service_components
        self.permission_policy_cls = permission_policy_cls

        self.validate()

        self.create_record_type()

    def _build_schema_path(self, optional_schema_path):
        """Build path for jsonschema."""
        if optional_schema_path:
            return optional_schema_path
        return self._schema_path_template.format(
            name_plural=self.name_plural,
            name=self.record_name_lower,
            version=self.schema_version,
        )

    def _build_index_name(self, index_name):
        """Build index name."""
        if index_name:
            return index_name
        return self._index_name_template.format(
            name_plural=self.name_plural,
            name=self.record_name_lower,
            version=self.schema_version,
        )

    def validate(self):
        """Validate parameters."""
        # TODO - specify what should be validated
        pass

    def create_record_type(self):
        """Create the record type."""
        # methods should call in this order, since classes have dependencies
        self.create_metadata_model()
        self.create_record_class()
        self.create_resource_class()
        self.create_service_class()

    def create_metadata_model(self):
        """Create metadata model."""
        model_class_attributes = {
            "__tablename__": f"{self.record_name_lower}_metadata",
            **self.model_cls_attrs,
        }

        self.model_cls = type(
            f"{self.record_type_name}Metadata",
            (db.Model, RecordMetadataBase),
            model_class_attributes,
        )

    def create_record_class(self):
        """Create record class."""
        pid_field = self.pid_field_cls(**self.pid_field_kwargs)

        record_class_attributes = {
            "model_cls": self.model_cls,
            "schema": ConstantField("$schema", self.schema_path),
            "index": IndexField(self.index_name),
            "pid": pid_field,
            "dumper": self.record_dumper or SearchDumper(),
        }

        record_class_attributes.update(self.record_cls_attrs)

        if self.record_relations:
            record_class_attributes["relations"] = self.record_relations

        self.record_cls = type(
            self.record_type_name, (Record,), record_class_attributes
        )

    def create_resource_class(self):
        """Create resource class."""
        resource_config_cls_name = f"{self.record_type_name}ResourceConfig"
        resource_cls_name = f"{self.record_type_name}Resource"

        config_cls_attributes = {
            "blueprint_name": self.record_name_lower,
            "url_prefix": self.endpoint_route or f"/{self.record_name_lower}s",
            **self.resource_cls_attrs,
        }

        self.resource_config_cls = type(
            resource_config_cls_name,
            (RecordResourceConfig,),
            config_cls_attributes,
        )

        self.resource_cls = type(resource_cls_name, (RecordResource,), {})

    def create_service_class(self):
        """Create service class."""
        permission_policy_cls_name = f"{self.record_type_name}PermissionPolicy"
        config_cls_name = f"{self.record_type_name}ServiceConfig"
        service_cls_name = f"{self.record_type_name}Service"

        # if permission policy not given, create a standard one
        if not self.permission_policy_cls:
            self.permission_policy_cls = type(
                permission_policy_cls_name, (RecordPermissionPolicy,), {}
            )

        route = self.endpoint_route or f"/{self.record_name_lower}s"

        config_cls_attributes = {
            "permission_policy_cls": self.permission_policy_cls,
            "record_cls": self.record_cls,
            "search": self.search_options,
            "schema": self.service_schema,
            "links_item": {
                "self": RecordLink("{+api}" + route + "/{id}"),
            },
            "links_search": pagination_links("{+api}" + route + "{?args*}"),
        }
        if self.service_components:
            config_cls_attributes.update({"components": self.service_components})

        if self.service_id:
            config_cls_attributes["service_id"] = self.service_id
            config_cls_attributes["indexer_queue_name"] = self.service_id

        self.service_config_cls = type(
            config_cls_name, (RecordServiceConfig,), config_cls_attributes
        )

        self.service_cls = type(service_cls_name, (RecordService,), {})
