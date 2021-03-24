# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 CERN.
# Copyright (C) 2021 Northwestern University.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Invenio Resources module to create REST APIs."""

from flask_resources import resource_requestctx
from werkzeug.http import quote_etag


def etag_headers(obj_or_list, code, many=False):
    """Headers for a single resource item."""
    headers = {
        'content-type': resource_requestctx.accept_mimetype,
    }
    if many:
        return headers

    etag = obj_or_list.get("revision_id")
    if etag:
        headers["ETag"] = quote_etag(str(etag), False)
    return headers
