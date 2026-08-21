# SPDX-FileCopyrightText: 2020 CERN.
# SPDX-FileCopyrightText: 2020 Northwestern University.
# SPDX-FileCopyrightText: 2025 CESNET i.a.l.e.
# SPDX-License-Identifier: MIT

"""File service results."""

from collections import defaultdict
from datetime import datetime
from functools import cached_property
from pathlib import Path

from flask import request, Response
from invenio_files_rest.helpers import send_stream

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
    def directories(self):
        """Iterator over the hits, expanding links for each directory entry."""
        directory_entries = defaultdict(list)
        for entry in self._listing.get("entries", []):
            directory_entries[str(Path(entry["key"]).parent)].append(entry["key"])
        for directory in self._listing.get("directories", []):
            self._expand_links(directory)
            directory["entries"] = directory_entries.get(directory["key"])
            yield directory

    def to_dict(self):
        """Return result as a dictionary."""
        return {
            **self._listing,
            "entries": list(self.entries),
            "directories": list(self.directories),
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

    def _get_mtime(self):
        """Extract modification time from the extracted stream if available.

        For ZIP members (ZipFileProxy), this extracts the date_time from the
        underlying ZipInfo and converts it to a Unix timestamp.

        Returns:
            Unix timestamp (float) or None if mtime cannot be determined.
        """
        # Try to get mtime from ZipFileProxy's _file_info (ZipInfo.date_time)
        if hasattr(self._extracted_stream, '_file_info'):
            file_info = self._extracted_stream._file_info
            if hasattr(file_info, 'date_time'):
                try:
                    dt = datetime(*file_info.date_time[:6])
                    return dt.timestamp()
                except (ValueError, TypeError):
                    pass

        # Try to get mtime attribute directly from the stream
        if hasattr(self._extracted_stream, 'mtime'):
            return self._extracted_stream.mtime

        return None

    def send_file(self, restricted=True, as_attachment=False):
        """Return file stream with HTTP Range support.

        Delegates to invenio_files_rest.helpers.send_stream() to ensure
        consistent behavior with regular file downloads, including:
        - Security headers (Content-Security-Policy, X-Content-Type-Options, etc.)
        - Mimetype sanitization
        - Cache control based on restricted parameter
        - Unicode-safe filename handling (RFC 5987)
        - HTTP Range request support (when FILES_REST_ALLOW_RANGE_REQUESTS is enabled)

        Args:
            restricted: When True, prevents caching by setting no-cache headers.
            as_attachment: When True, sets Content-Disposition to 'attachment'
                (forces download). When False, uses 'inline' (shows in browser).

        Performance note: Range requests on ZIP_DEFLATED members may require
        decompressing data from the beginning of the member to reach the
        requested offset. For large compressed files, consider using ZIP_STORED
        or implementing a materialized extraction cache for frequently accessed
        content.

        Returns:
            Flask Response object with appropriate headers and stream.
        """
        # Get filename from stream or fallback to file_id
        if getattr(self._extracted_stream, "name", None) is not None:
            filename = self._extracted_stream.name
        else:
            filename = self.file_id

        # Check if the stream is iterable (e.g., GeneratorReader for directory ZIPs)
        # These non-seekable streams cannot support Range requests
        if getattr(self._extracted_stream, "iterable", None) is not None:
            # For non-seekable streams, we need to handle them differently
            # since send_stream expects a proper file-like object

            chunk_iterator = self._extracted_stream.iterable
            disposition = "attachment" if as_attachment else "inline"

            headers = {
                "Content-Disposition": f'{disposition}; filename="{filename}"'
            }

            return Response(
                chunk_iterator,
                mimetype=self.mimetype or "application/octet-stream",
                headers=headers,
            )

        # For seekable streams (individual files from ZIP), use send_stream
        # which provides consistent security headers and Range support
        mtime = self._get_mtime()

        return send_stream(
            stream=self._extracted_stream,
            filename=filename,
            size=self.size,
            mtime=mtime,
            mimetype=self.mimetype,
            restricted=restricted,
            as_attachment=as_attachment,
        )
