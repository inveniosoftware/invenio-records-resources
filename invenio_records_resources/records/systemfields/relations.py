# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
# Copyright (C) 2020 Northwestern University.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Relations system field."""

from invenio_pidstore.models import PersistentIdentifier
from invenio_records.systemfields.relations import InvalidRelationValue, \
    ListRelation, RelationBase


class PIDRelation(RelationBase):
    """PID relation type."""

    def __init__(self, *args, pid_field=None, **kwargs):
        """Initialize the PK relation."""
        self.pid_field = pid_field
        super().__init__(*args, **kwargs)

    def resolve(self, id_):
        """Resolve the value using the record class."""
        try:
            return self.pid_field.resolve(id_)
        # TODO: there's many ways PID resolution can fail...
        except Exception:
            return None

    def parse_value(self, value):
        """Parse a record (or ID) to the ID to be stored."""
        if isinstance(value, str):
            return value
        elif isinstance(value, PersistentIdentifier):
            return value.pid_value
        elif isinstance(value, self.pid_field.record_cls):
            pid = getattr(self.pid_field.attr_name)
            return pid.pid_value
        else:
            raise InvalidRelationValue(
                f'Invalid value. Expected "str", a PID, or '
                f'"{self.pid_field.record_cls}"'
            )

    # TODO: We could have a more efficient "exists" via PK queries
    # def exists(self, id_):
    #     """Check if an ID exists using the record class."""
    #     return bool(self.record_cls.model_cls.query.filter_by(id=id_))
    #
    # def exists_many(self, ids):
    #     """."""
    #     self.record_cls.get_record(id_)


class PIDListRelation(ListRelation, PIDRelation):
    """PID list relation type."""
