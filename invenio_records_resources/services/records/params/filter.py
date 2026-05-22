# SPDX-FileCopyrightText: 2021 CERN.
# SPDX-License-Identifier: MIT

"""Facets parameter interpreter API."""

from functools import partial

from invenio_records_resources.services.records.params import ParamInterpreter


class FilterParam(ParamInterpreter):
    """Evaluate type filter."""

    def __init__(self, param_name, field_name, config):
        """."""
        self.param_name = param_name
        self.field_name = field_name
        super().__init__(config)

    @classmethod
    def factory(cls, param=None, field=None):
        """Create a new filter parameter."""
        return partial(cls, param, field)

    def apply(self, identity, search, params):
        """Applies a filter to get only records for a specific type."""
        # Pop because we don't want it to show up in links.
        # TODO: only pop if needed.
        value = params.pop(self.param_name, None)
        if value:
            if isinstance(value, str):
                search = search.filter("term", **{self.field_name: value})
            else:
                search = search.filter("terms", **{self.field_name: value})

        return search
