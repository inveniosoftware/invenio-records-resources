# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
# Copyright (C) 2020 Northwestern University.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Invenio Resources basic XML serialization module."""

import xmltodict
from flask_resources.serializers import SerializerMixin


class XMLSerializer(SerializerMixin):
    """Simplistic XML serializer."""

    def serialize_object(self, obj, response_ctx=None, *args, **kwargs):
        """Dump the object into an XML string."""
        return xmltodict.unparse({"root": obj})

    def serialize_object_list(
        self, obj_list, response_ctx=None, *args, **kwargs
    ):
        """Dump the object list into an XML string.

        :param: obj_list an IdentifiedRecords object
        """
        raise NotImplementedError()
