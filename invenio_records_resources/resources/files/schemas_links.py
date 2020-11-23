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
    """Schema for files list links."""

    # NOTE: /api prefix is needed here because above are mounted on /api
    self_ = Link(
        template=URITemplate("/api/records/{pid_value}/files"),
        permission="read",
        params=lambda record: {
            'pid_value': record.pid.pid_value,
        },
        data_key="self"  # To avoid using self since is python reserved key
    )


class FileLinksSchema(Schema):
    """Schema for a record file's links."""

    self_ = Link(
        template=URITemplate("/api/records/{pid_value}/files/{key}"),
        permission="read",
        params=lambda record_file: {
            'pid_value': record_file.record.pid.pid_value,
            'key': record_file.key,
        },
        data_key="self"  # To avoid using self since is python reserved key
    )

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
