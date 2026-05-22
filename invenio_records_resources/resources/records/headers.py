# SPDX-FileCopyrightText: 2021 CERN.
# SPDX-FileCopyrightText: 2021 Northwestern University.
# SPDX-License-Identifier: MIT

"""Invenio Resources module to create REST APIs."""

from flask_resources import resource_requestctx
from werkzeug.http import quote_etag


def etag_headers(obj_or_list, code, many=False):
    """Headers for a single resource item."""
    headers = {
        "content-type": resource_requestctx.accept_mimetype,
    }
    if many:
        return headers

    etag = obj_or_list.get("revision_id")
    if etag:
        headers["ETag"] = quote_etag(str(etag), False)
    return headers
