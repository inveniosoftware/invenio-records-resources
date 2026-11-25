# SPDX-FileCopyrightText: 2021 CERN.
# SPDX-FileCopyrightText: 2021 Northwestern University.
# SPDX-FileCopyrightText: 2026 RERO.
# SPDX-License-Identifier: MIT

"""Invenio Resources module to create REST APIs."""

import re

import marshmallow as ma
from flask_resources import resource_requestctx
from werkzeug.http import quote_etag


class ETagInteger(ma.fields.Integer):
    """Integer that also accepts an HTTP entity-tag.

    Responses carry ``ETag: "5"``, so a conformant client echoes that exact
    value back in ``If-Match``. A reverse proxy compressing the response
    downgrades the tag to ``W/"5"``, because the byte sequence changes. Both
    forms, and the bare integer accepted so far, load to the revision id.
    """

    #: Optional weak prefix, then the quoted tag -- RFC 9110, section 8.8.3.
    _ENTITY_TAG = re.compile(r'^(?:W/)?"(.*)"$')

    def _deserialize(self, value, attr, data, **kwargs):
        """Strip the entity-tag syntax before the integer conversion."""
        if isinstance(value, str):
            match = self._ENTITY_TAG.match(value.strip())
            if match:
                value = match.group(1)
        return super()._deserialize(value, attr, data, **kwargs)


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
