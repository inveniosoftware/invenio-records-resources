# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Records service copmonent base classes."""


class ServiceComponent:
    """Base service component."""

    schema = None

    def __init__(self, service):
        pass

    def create(self, record, identity, data):
        pass

    # TODO (Alex): is this needed?
    def read(self, record, identity):
        pass

    def update(self, record, identity, data):
        pass

    def delete(self, record, identity):
        pass

    def search(self, query, identity, **kwargs):
        return query


class MetadataComponent(ServiceComponent):
    """Service component for metadata."""

    def create(self, record, identity, data):
        validated_data = data['metadata']
        # TODO (Alex): use when `MetadataField(SystemField)` is implemented
        # record.metadata = validated_data
        record.update({'metadata': validated_data})

    def update(self, record, identity, data):
        validated_data = data['metadata']
        # TODO (Alex): use when `MetadataField(SystemField)` is implemented
        # record.metadata = validated_data
        record.update({'metadata': validated_data})


class PIDSComponent(ServiceComponent):
    """Service component for PIDs integration."""


class FilesComponent(ServiceComponent):
    """Service component for files integration."""


class AccessComponent(ServiceComponent):
    """Service component for access integration."""

    def create(self, record, identity, data):
        validated_data = data['access']
        # TODO (Alex): replace with `record.access = ...`
        validated_data.setdefault('created_by', identity.id)
        validated_data.setdefault('owners', [identity.id])
        record.update({'access': validated_data})
