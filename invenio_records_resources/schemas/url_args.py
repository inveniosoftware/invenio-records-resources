# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
# Copyright (C) 2020 Northwestern University.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Marshmallow JSON schema."""


from marshmallow import Schema, ValidationError, fields, post_load, validate, \
    validates_schema

from ..pagination import PagedIndexes

# TODO: Make configurable
DEFAULT_RESULTS_PER_PAGE = 25
DEFAULT_MAX_RESULTS = 10000


class PaginationURLArgsSchemaV1(Schema):
    """Schema for pagination URL args."""

    page = fields.Int(validate=validate.Range(min=1), missing=1)
    size = fields.Int(
        validate=validate.Range(min=1, max=DEFAULT_MAX_RESULTS),
        missing=DEFAULT_RESULTS_PER_PAGE
    )

    @validates_schema
    def validate_pagination(self, data, **kwargs):
        """Validate pagination args make sense."""
        page = PagedIndexes(data["size"], data["page"], DEFAULT_MAX_RESULTS)
        if not page.valid():
            raise ValidationError("Invalid pagination parameters.")

    @post_load
    def from_and_to_idx(self, data, **kwargs):
        """Inject from_idx and to_idx into data bc they are valid."""
        page = PagedIndexes(data["size"], data["page"], DEFAULT_MAX_RESULTS)
        data["from_idx"] = page.from_idx
        data["to_idx"] = page.to_idx
        return data


class SortURLArgsSchemaV1(Schema):
    """Schema for sorting URL arg."""

    sort_by = fields.Method(
        data_key="sort", serialize="unload_sort", deserialize="load_sort_by"
    )
    reverse = fields.Method(
        data_key="sort", load_only=True, deserialize="load_reverse"
    )

    def load_sort_by(self, data):
        """Deserializes 'sort_by' field from "sort" string.

        :param data: Field value (e.g. 'key' or '-key').
        :returns: 'key'
        """
        return data[1:] if data.startswith("-") else data

    def load_reverse(self, data):
        """Deserializes 'reverse' field from "sort" string.

        :param data: Field value (e.g. 'key' or '-key').
        :returns: False if '-key' else True
        """
        return data.startswith("-")

    def unload_sort(self, obj):
        """Serialize 'sort' field from 'sort_by' and 'reverse' fields."""
        prefix = "-" if obj.get("reverse", False) else ""
        return prefix + obj.get("sort_by", "")


class SearchURLArgsSchemaV1(PaginationURLArgsSchemaV1, SortURLArgsSchemaV1):
    """Schema for search URL args."""

    q = fields.String()
