# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 CERN.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Record providers."""

from invenio_pidstore.errors import PIDAlreadyExists


class ModelPIDProvider:
    """Record identifier provider for ModelPIDFields.

    It avoids subclassing `invenio_pidstore.providers.base.BaseProvider`
    since the behaviour is completely different and does not need
    any of the class attributes.
    """

    @classmethod
    def create(cls, pid_value, record, model_field_name, **kwargs):
        """Sets the pid in the record model.

        Checks for duplicates.
        """
        filters = {model_field_name: pid_value}
        obj = record.model_cls.query.filter_by(**filters).one_or_none()
        if obj:
            raise PIDAlreadyExists(
                pid_value=pid_value,
                pid_type=record.__class__.__name__,  # FIXME: is informative
            )
        setattr(record, model_field_name, pid_value)
