# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
# Copyright (C) 2020 Northwestern University.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Record schema."""

from marshmallow import Schema
from marshmallow_utils.fields import Link
from uritemplate import URITemplate


class FilesLinksSchema(Schema):
    """Schema for a record's links."""

    # NOTE: /api prefix is needed here because above are mounted on /api
    record = Link(
        template=URITemplate("/api/records/{pid_value}/files/{key}"),
        permission="read",
        params=lambda record: {'pid_value': record.pid.pid_value}
    )
    self_ = Link(
        template=URITemplate("/api/records/{pid_value}/files/{key}"),
        permission="read",
        params=lambda record_file: {
            'pid_value': record_file.record.pid.pid_value,
            'key': record_file.key,
        },
        data_key="self"  # To avoid using self since is python reserved key
    )


class FileLinksSchema(FilesLinksSchema):
    """Schema for a record's links."""

    # self and record are declared in the parent

    # TODO: Explore how to expose also the HTTP method
    # commit = {
    #   "href": URITemplate("/api/records/{pid_value}/files/{key}/commit"),
    #   "method": "POST",
    # }
    content = Link(
        template=URITemplate("/api/records/{pid_value}/files/{key}/content"),
        permission="read",
        params=lambda record_file: {
            'pid_value': record_file.record.pid.pid_value,
            'key': record_file.key,
        },
    )

    commit = Link(
        template=URITemplate("/api/records/{pid_value}/files/{key}/commit"),
        permission="read",
        params=lambda record_file: {
            'pid_value': record_file.record.pid.pid_value,
            'key': record_file.key,
        },
    )
