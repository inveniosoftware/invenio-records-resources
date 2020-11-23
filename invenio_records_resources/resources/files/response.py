# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Schemas for parameter parsing."""

from flask import Response as FlaskResponse

from ..records.response import RecordResponse


class RecordFileResponse(RecordResponse):
    """Class for streaming file responses."""

    def make_item_response(self, content, code=200):
        """Immediately returns response objects."""
        if isinstance(content, FlaskResponse):
            return content
        return super().make_item_response(content, code=code)
