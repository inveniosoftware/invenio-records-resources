# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
#
# Invenio-Resources is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Invenio Resources module to create REST APIs."""

from flask import make_response
from flask_resources.responses import Response


class RecordResponse(Response):
    """Record response representation."""

    def make_item_response(self, content, code):
        """Builds a response for a single object."""
        return make_response(
            self.serializer.serialize_object(content),
            code,
            self.make_headers(),
        )

    def make_list_response(self, content, code):
        """Builds a response for a list of objects."""
        return make_response(
            self.serializer.serialize_object_list(content),
            code,
            self.make_headers(),
        )
