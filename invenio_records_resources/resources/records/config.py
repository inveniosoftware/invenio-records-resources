# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
# Copyright (C) 2020 Northwestern University.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Record Resource Configuration."""

import marshmallow as ma
from flask_resources import (
    JSONDeserializer,
    JSONSerializer,
    RequestBodyParser,
    ResourceConfig,
    ResponseHandler,
)

from .args import SearchRequestArgsSchema
from .headers import etag_headers


class RecordResourceConfig(ResourceConfig):
    """Record resource config."""

    # Blueprint configuration
    blueprint_name = None
    url_prefix = "/records"
    routes = {
        "list": "",
        "item": "/<pid_value>",
    }

    # Request parsing
    request_read_args = {}
    request_view_args = {"pid_value": ma.fields.Str()}
    request_search_args = SearchRequestArgsSchema
    request_extra_args = {
        "expand": ma.fields.Boolean(),
        "refresh": ma.fields.Boolean(),
    }
    request_headers = {"if_match": ma.fields.Int()}
    request_body_parsers = {"application/json": RequestBodyParser(JSONDeserializer())}
    default_content_type = "application/json"

    # Response handling
    response_handlers = {
        "application/json": ResponseHandler(JSONSerializer(), headers=etag_headers)
    }
    default_accept_mimetype = "application/json"
