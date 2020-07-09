# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Generated field."""

import warnings

from marshmallow import missing as missing_

from .marshmallow_contrib import Function, Method


# FIXME: Is this even used?
class GeneratedValue(object):
    """Sentinel value class forcing marshmallow missing field generation."""

    pass


class ForcedFieldDeserializeMixin(object):
    """Mixin that forces deserialization of marshmallow fields."""

    # Overriding default deserializer since we need to deserialize an
    # initially non-existent field. In this implementation the checks are
    # removed since we expect our deserializer to provide the value.
    def deserialize(self, *args, **kwargs):
        """Deserialize field."""
        # Proceed with deserialization, skipping all checks.
        output = self._deserialize(*args, **kwargs)
        self._validate(output)
        return output


class GenFunction(ForcedFieldDeserializeMixin, Function):
    """Function field which is always deserialized."""

    pass


class GenMethod(ForcedFieldDeserializeMixin, Method):
    """Method field which is always deserialized."""

    pass
