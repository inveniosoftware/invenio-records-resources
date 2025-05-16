# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
# Copyright (C) 2020 Northwestern University.
# Copyright (C) 2025 CESNET.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""File service results."""

from ...proxies import current_transfer_registry
from ..base import ServiceListResult
from ..records.results import RecordItem


class FileItem(RecordItem):
    """List of file items result."""

    def __init__(self, service, identity, file_, record, errors=None, links_tpl=None):
        """Constructor."""
        super(FileItem, self).__init__(
            service,
            identity,
            record,
            errors=errors,
            links_tpl=links_tpl,
            schema=service.file_schema,
        )
        self._file = file_

    @property
    def file_id(self):
        """Get the record id."""
        return self._file.key

    @property
    def _obj(self):
        """Return the object to dump."""
        return self._file

    @property
    def links(self):
        """Get links for this result item."""
        _links = self._links_tpl.expand(self._identity, self._file)
        if "self" not in _links:
            return _links
        transfer = current_transfer_registry.get_transfer(
            file_record=self._file, file_service=self._service, record=self._record
        )
        for k, v in transfer.expand_links(self._identity, _links["self"]).items():
            if v is not None:
                _links[k] = v
            else:
                _links.pop(k, None)
        return _links

    def send_file(self, restricted=True, as_attachment=False):
        """Return file stream."""
        transfer = current_transfer_registry.get_transfer(
            file_record=self._file, file_service=self._service, record=self._record
        )
        return transfer.send_file(restricted=restricted, as_attachment=as_attachment)

    def open_stream(self, mode):
        """Return a file stream context manager."""
        return self._file.open_stream(mode)

    def get_stream(self, mode):
        """Return a file stream.

        It is up to the caller to close the steam.
        """
        return self._file.get_stream(mode)


class FileList(ServiceListResult):
    """List of file items result."""

    def __init__(
        self, service, identity, results, record, links_tpl=None, links_item_tpl=None
    ):
        """Constructor.

        :params service: a service instance
        :params identity: an identity that performed the service request
        :params results: the search results
        :params links_config: a links store config
        """
        self._identity = identity
        self._record = record
        self._results = results
        self._service = service
        self._links_tpl = links_tpl
        self._links_item_tpl = links_item_tpl

    @property
    def entries(self):
        """Iterator over the hits."""
        for entry in self._results:
            # Project the record
            projection = self._service.file_schema.dump(
                entry,
                context=dict(
                    identity=self._identity, record=self._record, service=self._service
                ),
            )

            # create links
            if self._links_item_tpl:
                links = self._links_item_tpl.expand(self._identity, entry)
            else:
                links = {}

            # add transfer links
            if "self" in links:
                transfer = current_transfer_registry.get_transfer(
                    file_record=entry, file_service=self._service, record=self._record
                )
                for k, v in transfer.expand_links(
                    self._identity, links["self"]
                ).items():
                    if v is not None:
                        links[k] = v
                    else:
                        links.pop(k, None)

            projection["links"] = links

            yield projection

    def to_dict(self):
        """Return result as a dictionary."""
        # TODO: Use a FilesSchema or something to dump the top-level object
        record_files = self._record.files
        result = {
            "enabled": record_files.enabled,
        }
        if self._links_tpl:
            result["links"] = self._links_tpl.expand(self._identity, self._record)

        if result["enabled"]:
            result.update(
                {
                    "entries": list(self.entries),
                    "default_preview": record_files.default_preview,
                    "order": record_files.order,
                }
            )
        return result
