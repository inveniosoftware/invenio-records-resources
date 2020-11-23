# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""File schema."""

from marshmallow import EXCLUDE, Schema
from marshmallow.fields import Dict, Number, Str
from marshmallow_utils.fields import Links


class FileSchema(Schema):
    """Schema for records v1 in JSON."""

    class Meta:
        """Meta class to reject unknown fields."""

        unknown = EXCLUDE

    key = Str()
    checksum = Str(attribute='file.checksum')
    size = Number(attribute='file.size')
    created = Str()
    updated = Str()
    links = Links()
    metadata = Dict()


class FileLinks(Schema):
    """Search links schema."""

    links = Links()


class FilesLinks(Schema):
    """Search links schema."""

    links = Links()
