# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
# Copyright (C) 2020 Northwestern University.
# Copyright (C) 2023 TU Wien.
# Copyright (C) 2025 Graz University of Technology.
# Copyright (C) 2025 CESNET.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Invenio Record File Resources."""

from contextlib import ExitStack

import marshmallow as ma
from flask import Response, current_app, g, request, stream_with_context
from flask_resources import (
    JSONDeserializer,
    RequestBodyParser,
    Resource,
    request_body_parser,
    request_parser,
    resource_requestctx,
    response_handler,
    route,
)
from invenio_stats.proxies import current_stats
from zipstream import ZIP_STORED, ZipStream

from ..errors import ErrorHandlersMixin
from .parser import RequestStreamParser

#
# Decorator helpers
#
request_view_args = request_parser(
    {"pid_value": ma.fields.Str(required=True), "key": ma.fields.Str()},
    location="view_args",
)

request_data = request_body_parser(
    parsers={"application/json": RequestBodyParser(JSONDeserializer())},
    default_content_type="application/json",
)

request_stream = request_body_parser(
    parsers={"application/octet-stream": RequestStreamParser()},
    default_content_type="application/octet-stream",
)

request_multipart_args = request_parser(
    {
        "pid_value": ma.fields.Str(required=True),
        "key": ma.fields.Str(),
        "part": ma.fields.Int(),
    },
    location="view_args",
)

request_multipart_args = request_parser(
    {
        "pid_value": ma.fields.Str(required=True),
        "key": ma.fields.Str(),
        "part": ma.fields.Int(),
    },
    location="view_args",
)


def set_max_content_length(func):
    """Set max content length."""

    def _wrapper(*args, **kwargs):
        # flask >= 3.1.0 changed the behavior of MAX_CONTENT_LENGTH
        # configuration variable. this is applied now to all requests
        # including file upload. File uploads have much higher file
        # size as form POST's. To keep request.max_content_length for
        # form posts on a small value the request.max_content_length
        # for file uploads is set here to the
        # FILES_REST_DEFAULT_MAX_FILE_SIZE
        request.max_content_length = current_app.config.get(
            "FILES_REST_DEFAULT_MAX_FILE_SIZE", 10**10
        )
        return func(*args, **kwargs)

    return _wrapper


#
# Resource
#
class FileResource(ErrorHandlersMixin, Resource):
    """File resource."""

    def __init__(self, config, service):
        """Constructor."""
        super(FileResource, self).__init__(config)
        self.service = service

    def create_url_rules(self):
        """Routing for the views."""
        routes = self.config.routes

        url_rules = [
            route("GET", routes["list"], self.search),
            route("GET", routes["item"], self.read),
            route("GET", routes["item-content"], self.read_content),
        ]

        # FileResourceConfig.allow_upload and .allow_archive_download are deprecated
        # in favor of FileServiceConfig.allow_upload and .allow_archive_download
        # instead. Fallbacks are used until complete removal and precedence
        # is given to FileResourceConfig until transition is complete.
        allow_archive_download = getattr(
            self.config,
            "allow_archive_download",
            self.service.config.allow_archive_download,
        )
        allow_upload = getattr(
            self.config, "allow_upload", self.service.config.allow_upload
        )

        if allow_archive_download:
            url_rules += [
                route("GET", routes["list-archive"], self.read_archive),
            ]
        if allow_upload:
            url_rules += [
                route("POST", routes["list"], self.create),
                route("DELETE", routes["list"], self.delete_all),
                route("PUT", routes["item"], self.update),
                route("DELETE", routes["item"], self.delete),
                route("POST", routes["item-commit"], self.create_commit),
                route("PUT", routes["item-content"], self.update_content),
            ]
            if "item-multipart-content" in routes:
                # allow multipart upload to local storage if the route is defined
                url_rules += [
                    route(
                        "PUT",
                        routes["item-multipart-content"],
                        self.upload_multipart_content,
                    ),
                ]
        return url_rules

    @request_view_args
    @response_handler(many=True)
    def search(self):
        """List files."""
        files = self.service.list_files(
            g.identity,
            resource_requestctx.view_args["pid_value"],
        )
        return files.to_dict(), 200

    @request_view_args
    def delete_all(self):
        """Delete all files."""
        self.service.delete_all_files(
            g.identity,
            resource_requestctx.view_args["pid_value"],
        )

        return "", 204

    @request_view_args
    @request_data
    @response_handler()
    def create(self):
        """Initialize an upload on a record."""
        item = self.service.init_files(
            g.identity,
            resource_requestctx.view_args["pid_value"],
            resource_requestctx.data or [],
        )
        return item.to_dict(), 201

    @request_view_args
    @response_handler()
    def read(self):
        """Read a single file."""
        item = self.service.read_file_metadata(
            g.identity,
            resource_requestctx.view_args["pid_value"],
            resource_requestctx.view_args["key"],
        )

        return item.to_dict(), 200

    @request_view_args
    @request_data
    @response_handler()
    def update(self):
        """Update the metadata a single file."""
        item = self.service.update_file_metadata(
            g.identity,
            resource_requestctx.view_args["pid_value"],
            resource_requestctx.view_args["key"],
            resource_requestctx.data or {},
        )

        return item.to_dict(), 200

    @request_view_args
    def delete(self):
        """Delete a file."""
        self.service.delete_file(
            g.identity,
            resource_requestctx.view_args["pid_value"],
            resource_requestctx.view_args["key"],
        )

        return "", 204

    @request_view_args
    @response_handler()
    def create_commit(self):
        """Commit a file."""
        item = self.service.commit_file(
            g.identity,
            resource_requestctx.view_args["pid_value"],
            resource_requestctx.view_args["key"],
        )
        return item.to_dict(), 200

    @request_view_args
    def read_content(self):
        """Read file content."""
        item = self.service.get_file_content(
            g.identity,
            resource_requestctx.view_args["pid_value"],
            resource_requestctx.view_args["key"],
        )

        # emit file download stats event
        obj = item._file.object_version
        emitter = current_stats.get_event_emitter("file-download")
        if obj is not None and emitter is not None:
            emitter(current_app, record=item._record, obj=obj, via_api=True)

        return item.send_file()

    @request_view_args
    def read_archive(self):
        """Read a zipped version of all files."""
        id_ = resource_requestctx.view_args["pid_value"]
        files = self.service.list_files(g.identity, id_)

        # emit file download stats events for each file
        emitter = current_stats.get_event_emitter("file-download")
        for f in files._results:
            obj = f.object_version
            if obj is not None and emitter is not None:
                emitter(current_app, record=files._record, obj=obj, via_api=True)

        def _gen_zipstream():
            """Generator for the streaming of the zipped file."""
            zs = ZipStream(compress_type=ZIP_STORED)
            with ExitStack() as stack:
                for file_obj in files._results:
                    if file_obj.file is not None:
                        fp = stack.enter_context(file_obj.open_stream("rb"))
                        zs.add(fp, file_obj.key)
                yield from zs.all_files()
                yield from zs.finalize()

        return Response(
            stream_with_context(_gen_zipstream()),
            mimetype="application/zip",
            headers={
                "Content-Disposition": f"attachment; filename={id_}.zip",
            },
        )

    @set_max_content_length
    @request_view_args
    @request_stream
    @response_handler()
    def update_content(self):
        """Upload file content."""
        # TODO: Parse in `resource_requestctx`
        item = self.service.set_file_content(
            g.identity,
            resource_requestctx.view_args["pid_value"],
            resource_requestctx.view_args["key"],
            resource_requestctx.data["request_stream"],
            content_length=resource_requestctx.data["request_content_length"],
        )

        return item.to_dict(), 200

    @request_multipart_args
    @request_stream
    @response_handler()
    def upload_multipart_content(self):
        """Upload multipart file content."""
        item = self.service.set_multipart_file_content(
            g.identity,
            resource_requestctx.view_args["pid_value"],
            resource_requestctx.view_args["key"],
            resource_requestctx.view_args["part"],
            resource_requestctx.data["request_stream"],
            content_length=resource_requestctx.data["request_content_length"],
        )

        return item.to_dict(), 200
