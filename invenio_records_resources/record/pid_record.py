# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2020 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Record module."""

from invenio_records.api import Record
from invenio_db import db

from ..resource_units import IdentifiedRecord
from ..schemas import MetadataSchemaJSONV1
from ..services.data_validator import MarshmallowDataValidator
from .pid_manager import PIDManager


class PIDRecord(Record):
    """Persistent identifier manager."""

    # Config cls
    schema_cls=MetadataSchemaJSONV1
    resource_unit_cls = IdentifiedRecord

    # Instances
    data_validator = MarshmallowDataValidator(schema=schema_cls)
    pid_manager = PIDManager()

    @classmethod
    def create(cls, data):
        """Registers a record.
        - Validates the record, based on the `scheme`. A Marshmallow
          independent validator can be used by setting the `data_validator`
          property.
        - Creates the record
        - Creates and associates (mint) the PID to the record UUID. The PID is
          `REGISTERED` by default.

        :return: a resource unit instance with the pid and the record.
        """
        cls.data_validator.validate(data)
        record = super().create(data)  # Create record in DB
        pid = cls.pid_manager.create(record)
        db.session.commit()  # Persist DB

        return cls.resource_unit_cls(pid=pid, record=record)

    @classmethod
    def register(cls, pid):
        self.pid.register()

    @classmethod
    def get_from_id(cls, id_):
        return cls.resource_unit_cls(*cls.pid_manager.resolve(id_))



