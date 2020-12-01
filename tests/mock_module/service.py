# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
# Copyright (C) 2020 Northwestern University.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Example service."""

from invenio_records_resources.services import RecordFileService, \
    RecordFileServiceConfig
from invenio_records_resources.services.records.schema import RecordSchema
from invenio_records_resources.services.records.search import terms_filter

from .api import Record, RecordWithFile
from .permissions import PermissionPolicy


class ServiceConfig(RecordFileServiceConfig):
    """Mock service configuration.

    Needs both configs, with File overwritting the record ones.
    """

    permission_policy_cls = PermissionPolicy
    record_cls = Record
    schema = RecordSchema
    search_facets_options = {
        'aggs': {
            'type': {
                'terms': {'field': 'metadata.type.type'},
                'aggs': {
                    'subtype': {
                        'terms': {'field': 'metadata.type.subtype'},
                    }
                }
            }
        },
        'post_filters': {
            'subtype': terms_filter('metadata.type.subtype'),
            'type': terms_filter('metadata.type.type'),
        }
    }


class Service(RecordFileService):
    """Mock service."""

    default_config = ServiceConfig


class FileServiceConfig(RecordFileServiceConfig):
    """Mock service configuration."""

    permission_policy_cls = PermissionPolicy
    record_cls = RecordWithFile


class FileService(RecordFileService):
    """Mock service."""

    default_config = FileServiceConfig
