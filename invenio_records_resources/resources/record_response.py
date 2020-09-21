# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
# Copyright (C) 2020 Northwestern University.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Schemas for parameter parsing."""


from flask_resources.responses import Response
from werkzeug.http import quote_etag


class RecordResponse(Response):
    """Class to add `ETag` to response headers.

    NOTE: This class should ideally be removed when header serialization
        is implemented in `flask-resources`.
    """

    def make_headers(self, content=None):
        """Add `ETag` header to response."""
        headers = super().make_headers(content=content)
        etag = content.get("revision_id") if content else None
        if etag:
            headers["ETag"] = quote_etag(str(etag), False)
        return headers
