# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
# Copyright (C) 2020 Northwestern University.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Invenio Record File Resources."""

from contextlib import ExitStack

import marshmallow as ma
from flask import Response, abort, g, stream_with_context
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
        if self.config.allow_archive_download:
            url_rules += [
                route("GET", routes["list-archive"], self.read_archive),
            ]
        if self.config.allow_upload:
            url_rules += [
                route("POST", routes["list"], self.create),
                route("DELETE", routes["list"], self.delete_all),
                route("PUT", routes["item"], self.update),
                route("DELETE", routes["item"], self.delete),
                route("POST", routes["item-commit"], self.create_commit),
                route("PUT", routes["item-content"], self.update_content),
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

        if item is None:
            abort(404)

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

        if item is None:
            abort(404)

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

        if item is None:
            abort(404)

        return item.send_file(), 200

    @request_view_args
    def read_archive(self):
        """Read a zipped version of all files."""
        id_ = resource_requestctx.view_args["pid_value"]
        files = self.service.list_files(g.identity, id_)

        def _gen_zipstream():
            """Generator for the streaming of the zipped file."""
            zs = ZipStream(compress_type=ZIP_STORED)
            with ExitStack() as stack:
                for file_obj in files._results:
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

        if item is None:
            abort(404)

        return item.to_dict(), 200
