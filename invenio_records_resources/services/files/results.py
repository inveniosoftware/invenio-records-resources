# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
# Copyright (C) 2020 Northwestern University.
# Copyright (C) 2025 CESNET i.a.l.e.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""File service results."""

from collections import defaultdict
from functools import cached_property
from pathlib import Path

from flask import Response, current_app

from ...proxies import current_transfer_registry
from ..base import ServiceItemResult, ServiceListResult
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


class ContainerListResult(ServiceListResult):
    """Listing result for an archived file."""

    def __init__(self, service, identity, listing, item_template=None):
        """Init the listing result."""
        self._service = service
        self._identity = identity
        self._listing = listing
        self._item_template = item_template

    def _expand_links(self, container_item_metadata):
        """Expand links in entry."""
        # Add links only to files
        if self._item_template:
            container_item_metadata["links"] = self._item_template.expand(
                self._identity, container_item_metadata
            )

    @cached_property
    def entries(self):
        """Iterator over the hits, expanding links for each file entry."""
        for entry in self._listing.get("entries", []):
            self._expand_links(entry)
            yield entry

    @cached_property
    def folders(self):
        """Iterator over the hits, expanding links for each folder entry."""
        folder_entries = defaultdict(list)
        for entry in self._listing.get("entries", []):
            folder_entries[str(Path(entry["key"]).parent)].append(entry["key"])
        for folder in self._listing.get("folders", []):
            self._expand_links(folder)
            folder["entries"] = folder_entries.get(folder["key"])
            yield folder

    def to_dict(self):
        """Return result as a dictionary."""
        return {
            **self._listing,
            "entries": list(self.entries),
            "folders": list(self.folders),
        }


class ContainerItemResult(ServiceItemResult):
    """Extracted archived file item(s) with a send_file defined function."""

    def __init__(
        self,
        service,
        identity,
        record,
        file_record,
        extracted_stream,
        extracted_path,
        size=None,
        mimetype=None,
    ):
        """Constructor."""
        self._service = service
        self._identity = identity
        self._extracted_stream = extracted_stream
        self._extracted_path = extracted_path
        self.size = size
        self.mimetype = mimetype
        self._record = record
        self._file_record = file_record

    @property
    def file_id(self):
        """Get the record id."""
        return Path(self._extracted_path).name

    def send_file(self, restricted=True, as_attachment=False):
        """Return file stream."""
        if getattr(self._extracted_stream, "name", None) is not None:
            filename = self._extracted_stream.name
        else:
            filename = self.file_id
        if getattr(self._extracted_stream, "iterable", None) is not None:
            chunk_iterator = self._extracted_stream.iterable
        else:
            chunk_size = current_app.config[
                "RECORDS_RESOURCES_EXTRACTED_STREAM_CHUNK_SIZE"
            ]

            def generator():
                while True:
                    chunk = self._extracted_stream.read(chunk_size)
                    if not chunk:
                        break
                    yield chunk

                self._extracted_stream.close()

            chunk_iterator = generator()

        headers = {
            "Content-Disposition": f'attachment; filename="{filename}"',
        }
        if self.size is not None:
            headers["Content-Length"] = str(self.size)

        return Response(
            chunk_iterator,
            mimetype=self.mimetype or "application/octet-stream",
            headers=headers,
        )
