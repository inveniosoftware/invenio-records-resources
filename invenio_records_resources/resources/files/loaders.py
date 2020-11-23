# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Files loaders."""

from flask import request
from flask_resources.deserializers import DeserializerMixin
from flask_resources.loaders import RequestLoader


class StreamDeserializer(DeserializerMixin):
    """Stream deserializer."""

    def deserialize_data(self, data, *args, **kwargs):
        """Deserializes a stream."""
        return data


class RequestStreamLoader(RequestLoader):
    """Loaded request representation for streams."""

    def __init__(self, deserializer=None, args_parser=None, *args, **kwargs):
        """Constructor."""
        self.deserializer = deserializer or StreamDeserializer()
        self.args_parser = args_parser

    def load_data(self):
        """Load data from request stream."""
        return request.stream

    def load_item_request(self, *args, **kwargs):
        """Build request context."""
        return {
            "request_stream": request.stream,
            "request_content_length": request.content_length,
        }
