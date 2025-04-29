# -*- coding: utf-8 -*-
#
# Copyright (C) 2020-2024 CERN.
# Copyright (C) 2020-2022 Northwestern University.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Service results."""

from abc import ABC, abstractmethod

from invenio_access.permissions import system_user_id
from invenio_records.dictutils import dict_lookup, dict_merge, dict_set

from invenio_records_resources.services.base.results import (
    ServiceBulkItemResult,
    ServiceBulkListResult,
)

from ...pagination import Pagination
from ..base import ServiceItemResult, ServiceListResult


class RecordItem(ServiceItemResult):
    """Single record result."""

    def __init__(
        self,
        service,
        identity,
        record,
        errors=None,
        links_tpl=None,
        schema=None,
        expandable_fields=None,
        expand=False,
        nested_links_item=None,
    ):
        """Constructor."""
        self._errors = errors
        self._identity = identity
        self._links_tpl = links_tpl
        self._record = record
        self._service = service
        self._schema = schema or service.schema
        self._fields_resolver = FieldsResolver(expandable_fields)
        self._expand = expand
        self._nested_links_item = nested_links_item
        self._data = None

    @property
    def id(self):
        """Get the record id."""
        return self._record.pid.pid_value

    def __getitem__(self, key):
        """Key a key from the data."""
        return self.data[key]

    @property
    def links(self):
        """Get links for this result item."""
        return self._links_tpl.expand(self._identity, self._record)

    @property
    def _obj(self):
        """Return the object to dump."""
        return self._record

    @property
    def data(self):
        """Property to get the record."""
        if self._data:
            return self._data

        self._data = self._schema.dump(
            self._obj,
            context=dict(
                identity=self._identity,
                record=self._record,
            ),
        )
        if self._links_tpl:
            self._data["links"] = self.links

        if self._nested_links_item:
            for link in self._nested_links_item:
                link.expand(self._identity, self._record, self._data)

        if self._expand and self._fields_resolver:
            self._fields_resolver.resolve(self._identity, [self._data])
            fields = self._fields_resolver.expand(self._identity, self._data)
            self._data["expanded"] = fields

        return self._data

    @property
    def errors(self):
        """Get the errors."""
        return self._errors

    def to_dict(self):
        """Get a dictionary for the record."""
        res = self.data
        if self._errors:
            res["errors"] = self._errors
        return res

    def has_permissions_to(self, actions):
        """Returns dict of "can_<action>": bool.

        Placing this functionality here because it is a projection of the
        record item's characteristics and allows us to re-use the
        underlying data layer record. Because it is selective about the actions
        it checks for performance reasons, it is not embedded in the `to_dict`
        method.

        :params actions: list of action strings
        :returns dict:

        Example:
        record_item.permissions_to(["update_draft", "read_files"])
        {
            "can_update_draft": False,
            "can_read_files": True
        }
        """
        return {
            f"can_{action}": self._service.check_permission(
                self._identity, action, record=self._record
            )
            for action in actions
        }


class RecordList(ServiceListResult):
    """List of records result."""

    def __init__(
        self,
        service,
        identity,
        results,
        params=None,
        links_tpl=None,
        links_item_tpl=None,
        nested_links_item=None,
        schema=None,
        expandable_fields=None,
        expand=False,
    ):
        """Constructor.

        :params service: a service instance
        :params identity: an identity that performed the service request
        :params results: the search results
        :params params: dictionary of the query parameters
        """
        self._identity = identity
        self._results = results
        self._service = service
        self._schema = schema or service.schema
        self._params = params
        self._links_tpl = links_tpl
        self._links_item_tpl = links_item_tpl
        self._nested_links_item = nested_links_item
        self._fields_resolver = FieldsResolver(expandable_fields)
        self._expand = expand

    def __len__(self):
        """Return the total numer of hits."""
        return self.total

    def __iter__(self):
        """Iterator over the hits."""
        return self.hits

    @property
    def total(self):
        """Get total number of hits."""
        if hasattr(self._results, "hits"):
            return self._results.hits.total["value"]
        else:
            # handle scan(): returns a generator
            return None

    @property
    def aggregations(self):
        """Get the search result aggregations."""
        # TODO: have a way to label or not label
        try:
            return self._results.labelled_facets.to_dict()
        except AttributeError:
            return None

    @property
    def hits(self):
        """Iterator over the hits."""
        for hit in self._results:
            # Load dump
            record = self._service.record_cls.loads(hit.to_dict())

            # Project the record
            projection = self._schema.dump(
                record,
                context=dict(
                    identity=self._identity,
                    record=record,
                    meta=hit.meta,
                ),
            )
            if self._links_item_tpl:
                projection["links"] = self._links_item_tpl.expand(
                    self._identity, record
                )
            if self._nested_links_item:
                for link in self._nested_links_item:
                    link.expand(self._identity, record, projection)

            yield projection

    @property
    def pagination(self):
        """Create a pagination object."""
        return Pagination(
            self._params["size"],
            self._params["page"],
            self.total,
        )

    def to_dict(self):
        """Return result as a dictionary."""
        # TODO: This part should imitate the result item above. I.e. add a
        # "data" property which uses a ServiceSchema to dump the entire object.
        hits = list(self.hits)

        if self._expand and self._fields_resolver:
            self._fields_resolver.resolve(self._identity, hits)
            for hit in hits:
                fields = self._fields_resolver.expand(self._identity, hit)
                hit["expanded"] = fields

        res = {
            "hits": {
                "hits": hits,
                "total": self.total,
            }
        }

        if self.aggregations:
            res["aggregations"] = self.aggregations

        if self._params:
            res["sortBy"] = self._params["sort"]
            if self._links_tpl:
                res["links"] = self._links_tpl.expand(self._identity, self.pagination)

        return res


class RecordBulkItem(ServiceBulkItemResult):
    """Record bulk item."""

    def __init__(self, op_type, record, errors, exc):
        """Constructor."""
        self._op_type = op_type
        self._record = record
        self._errors = errors
        self._exc = exc

    @property
    def op_type(self):
        """Get operation type."""
        return self._op_type

    @property
    def record(self):
        """Get record."""
        return self._record

    @property
    def errors(self):
        """Get errors."""
        return self._errors

    @property
    def exc(self):
        """Get exception."""
        return self._exc


class RecordBulkList(ServiceBulkListResult):
    """List of records result."""

    def __init__(
        self,
        service,
        identity,
        results,
    ):
        """Constructor.

        :params service: a service instance
        :params identity: an identity that performed the service request
        :params results: the results of the bulk operation
        """
        self._identity = identity
        self._service = service
        self._results = [RecordBulkItem(*r) for r in results]

    @property
    def results(self):
        """Iterator over the results."""
        return iter(self._results)


class ExpandableField(ABC):
    """Field referencing to another record that can be expanded."""

    def __init__(self, field_name):
        """Constructor.

        :params field_name: the name of the field containing the value to
                           resolve the referenced record
        :params service: the service to fetch the referenced record
        """
        self._field_name = field_name
        self._service_values = dict()

    @property
    def field_name(self):
        """Return field name."""
        return self._field_name

    @abstractmethod
    def get_value_service(self, value):
        """Return the value and the service to fetch the referenced record.

        Example:
            return (value, MyService())
        """
        raise NotImplementedError()

    @abstractmethod
    def ghost_record(self, value):
        """Return the ghost representation of the unresolved value.

        This is used when a value cannot be resolved. The returned value
        will be available when the method `self.pick()` is called.
        """
        raise NotImplementedError()

    @abstractmethod
    def system_record(self):
        """Return the representation of a system user.

        This is used for the user with id = 'system'.
        """
        raise NotImplementedError()

    def has(self, service, value):
        """Return true if field has given value for given service."""
        try:
            self._service_values[service][value]
        except KeyError:
            return False
        return True

    def add_service_value(self, service, value):
        """Store each value in the list of results for this field."""
        self._service_values.setdefault(service, dict())
        self._service_values[service].setdefault(value, None)

    def add_dereferenced_record(self, service, value, resolved_rec):
        """Save the dereferenced record."""
        # mark the record as a "ghost" or "system" record i.e not resolvable
        if resolved_rec is None:
            if value == system_user_id:
                resolved_rec = self.system_record()
            else:
                resolved_rec = self.ghost_record({"id": value})
        self._service_values[service][value] = resolved_rec

    def get_dereferenced_record(self, service, value):
        """Return the dereferenced record."""
        return self._service_values[service][value]

    @abstractmethod
    def pick(self, identity, resolved_rec):
        """Pick the fields to return from the resolved record dict."""
        raise NotImplementedError()


class FieldsResolver:
    """Resolve the reference record for each of the configured field.

    Given a list of fields referencing other records/objects,
    it fetches and returns the dereferenced record/obj.

    To minimize the performance impact of resolving reference record, this
    object will:
    - first, collect all the possible values of each fields, grouping them
      by service to be called to fetch the referenced record/obj
    - it will then call the `service.read_many([ids])` method so that all
      reference records are retrieved with one search per service type
    - for each of the result to be returned, it will call the `pick` method
      of each configured field to allow to choose what fields should be
      selected and returned from the resolved record.

    It supports resolution of nested fields out of the box.
    """

    def __init__(self, expandable_fields):
        """Constructor.

        :params expandable_fields: list of ExpandableField obj.
        """
        self._fields = expandable_fields

    def _collect_values(self, hits):
        """Collect all field values to be expanded."""
        grouped_values = dict()
        for hit in hits:
            for field in self._fields:
                try:
                    value = dict_lookup(hit, field.field_name)
                    if value is None:
                        continue
                except KeyError:
                    continue
                else:
                    # value is not None
                    v, service = field.get_value_service(value)
                    field.add_service_value(service, v)
                    # collect values (ids) and group by service e.g.:
                    # service_1: (13, 4),
                    # service_2: (uuid1, uuid2, ...)
                    grouped_values.setdefault(service, set())
                    grouped_values[service].add(v)

        return grouped_values

    def _find_fields(self, service, value):
        """Find all fields matching service and value.

        The `id` field used to match the resolved record is hardcoded,
        as in the `read_many` method.
        """
        fields = []
        for field in self._fields:
            if field.has(service, value):
                fields.append(field)
        return fields

    def _fetch_referenced(self, grouped_values, identity):
        """Search and fetch referenced recs by ids."""

        def _add_dereferenced_record(service, value, resolved_rec):
            """Helper function to set the dereferenced record to the service."""
            for field in self._find_fields(service, value):
                field.add_dereferenced_record(service, value, resolved_rec)

        for service, all_values in grouped_values.items():
            results = service.read_many(identity, list(all_values))

            found_values = set()
            for hit in results.hits:
                value = hit.get("id", None)
                # keep values visited so we can extract the ones not found i.e ghost
                found_values.add(value)
                _add_dereferenced_record(service, value, hit)

            ghost_values = all_values - found_values
            if ghost_values:
                for value in ghost_values:
                    # set dereferenced record to None. That will trigger eventually
                    # the field.ghost_record() to be called
                    _add_dereferenced_record(service, value, None)

    def resolve(self, identity, hits):
        """Collect field values and resolve referenced records."""
        _hits = list(hits)  # ensure it is a list, when a single value passed
        grouped_values = self._collect_values(_hits)
        self._fetch_referenced(grouped_values, identity)

    def expand(self, identity, hit):
        """Return the expanded fields for the given hit."""
        results = dict()
        for field in self._fields:
            try:
                value = dict_lookup(hit, field.field_name)
                if value is None:
                    continue
            except KeyError:
                continue
            else:
                # value is not None
                v, service = field.get_value_service(value)
                resolved_rec = field.get_dereferenced_record(service, v)
                if not resolved_rec:
                    continue
                output = field.pick(identity, resolved_rec)

                # transform field name (potentially dotted) to nested dicts
                # to keep the nested structure of the field
                d = dict()
                dict_set(d, field.field_name, output)
                # merge dict with previous results
                dict_merge(results, d)

        return results
