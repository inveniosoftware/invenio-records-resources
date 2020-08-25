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
    ascending = fields.Method(
        data_key="sort", load_only=True, deserialize="load_ascending"
    )

    def load_sort_by(self, data):
        """Loads 'sort_by' field from "sort" string.

        :param data: Field value (e.g. 'key' or '-key').
        :returns: 'key'
        """
        if data.startswith("-"):
            return data[1:]
        return data

    def load_ascending(self, data):
        """Loads 'ascending' field from "sort" string.

        :param data: Field value (e.g. 'key' or '-key').
        :returns: False if '-key' else True
        """
        if data.startswith("-"):
            return False
        return True

    def unload_sort(self, obj):
        """Serialize 'sort' field from 'sort_by' and 'ascending' fields."""
        prefix = "-" if not obj.get("ascending", True) else ""
        return prefix + obj.get("sort_by", "")

    # sort_arg_name = 'sort'
    # urlfield = request.values.get(sort_arg_name, '', type=str)

    # # Get default sorting if sort is not specified.
    # if not urlfield:
    #     # cast to six.text_type to handle unicodes in Python 2
    #     has_query = request.values.get('q', type=six.text_type)
    #     urlfield = current_app.config['RECORDS_REST_DEFAULT_SORT'].get(
    #         index, {}).get('query' if has_query else 'noquery', '')

    # # Parse sort argument
    # key, asc = parse_sort_field(urlfield)

    # # Get sort options
    # sort_options = current_app.config['RECORDS_REST_SORT_OPTIONS'].get(
    #     index, {}).get(key)
    # if sort_options is None:
    #     return (search, {})

    # # Get fields to sort query by
    # search = search.sort(
    #     *[eval_field(f, asc) for f in sort_options['fields']]
    # )
    # return (search, {sort_arg_name: urlfield})


class SearchURLArgsSchemaV1(PaginationURLArgsSchemaV1, SortURLArgsSchemaV1):
    """Schema for search URL args."""

    q = fields.String()
