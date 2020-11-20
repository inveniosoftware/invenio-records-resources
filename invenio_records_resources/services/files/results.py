# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
# Copyright (C) 2020 Northwestern University.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""File service results."""

from marshmallow_utils.links import LinksFactory

from ..base import ServiceItemResult, ServiceListResult
from ..records.results import RecordItem, RecordList, _current_host


# FIXME: This two classes (FileItem and FileList) can simply injerit more
# if the schema is customizable in the function? See e.g. `data()` only changes
# `self._service.{schema|file_schema}.dump()` compared to RecordItem.
class FileItem(RecordItem):
    """List of file items result."""

    def __init__(self, service, identity, file_, record, errors=None,
                 links_config=None):
        """Constructor."""
        super(FileItem, self).__init__(
            service, identity, record, errors, links_config)
        self._file = file_

    @property
    def file_id(self):
        """Get the record id."""
        return self._file.key

    @property
    def data(self):
        """Property to get the record."""
        if self._data:
            return self._data

        links = LinksFactory(host=_current_host, config=self._links_config)

        self._data = self._service.file_schema.dump(
            self._identity,
            self._file,
            links_namespace="file",
            links_factory=links,
        )

        return self._data


class FileList(ServiceListResult):
    """List of file items result."""

    def __init__(self, service, identity, results, params,
                 links_config=None):
        """Constructor.

        :params service: a service instance
        :params identity: an identity that performed the service request
        :params results: the search results
        :params links_config: a links store config
        """
        self._identity = identity
        self._links_config = links_config
        self._results = results
        self._service = service
        self._links = None

    def __len__(self):
        """Return the total numer of hits."""
        return self.total

    def __iter__(self):
        """Iterator over the hits."""
        return self.results

    @property
    def links(self):
        """Get the search result links."""
        if self._links:
            return self._links

        links = LinksFactory(host=_current_host, config=self._links_config)
        schema = self._service.schema_files_links

        data = schema.dump(
            self._identity,
            links_factory=links,
            links_namespace="files",
        )
        self._links = data.get("links")

        return self._links

    @property
    def entries(self):
        """Iterator over the hits."""
        links = LinksFactory(host=_current_host, config=self._links_config)

        for entry in self._results:
            # Project the record
            projection = self._service.file_schema.dump(
                self._identity,
                entry,
                links_namespace="file",
                links_factory=links,
            )

            yield projection

    def to_dict(self):
        """Return result as a dictionary."""
        result = {
            "entries": list(self.entries),
        }
        if self._links:
            result['links'] = self._links

        return result


class RecordFileItem(RecordItem):
    """Single record with files result."""


class RecordFileList(RecordList):
    """List of records with files result."""
