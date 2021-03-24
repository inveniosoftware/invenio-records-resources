# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
# Copyright (C) 2020 Northwestern University.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Example service."""

from invenio_records_resources.services import FileServiceConfig, \
    RecordServiceConfig, SearchOptions
from invenio_records_resources.services.files.links import FileLink
from invenio_records_resources.services.records.config import SearchOptions
from invenio_records_resources.services.records.links import RecordLink, \
    pagination_links
from invenio_records_resources.services.records.schema import RecordSchema
from invenio_records_resources.services.records.search import terms_filter

from .api import Record, RecordWithFile
from .permissions import PermissionPolicy


class MockSearchOptions(SearchOptions):
    """Mock module search options."""

    facets_options = {
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


class ServiceConfig(RecordServiceConfig):
    """Mock service configuration.

    Needs both configs, with File overwritting the record ones.
    """

    permission_policy_cls = PermissionPolicy
    record_cls = Record
    schema = RecordSchema
    search = MockSearchOptions

    links_item = {
        "self": RecordLink("{+api}/mocks/{id}"),
        "files": RecordLink("{+api}/mocks/{id}/files"),
    }

    links_search = pagination_links("{+api}/mocks{?args*}")


class ServiceWithFilesConfig(ServiceConfig):
    """Config for service with files support."""

    record_cls = RecordWithFile


class MockFileServiceConfig(FileServiceConfig):
    """File service configuration."""

    record_cls = RecordWithFile
    permission_policy_cls = PermissionPolicy

    file_links_list = {
        "self": RecordLink("{+api}/mocks/{id}/files"),
    }

    file_links_item = {
        "self": FileLink("{+api}/mocks/{id}/files/{key}"),
        "content": FileLink("{+api}/mocks/{id}/files/{key}/content"),
        "commit": FileLink("{+api}/mocks/{id}/files/{key}/commit"),
    }
