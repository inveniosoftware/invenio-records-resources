# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 CERN.
#
# Invenio-RDM-Records is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Custom Fields for InvenioRDM."""

from marshmallow import fields

from .base import BaseCF

# FIXME: this should live in `invenio-vocabularies`
# the marsh schema would be there.
# https://github.com/inveniosoftware/invenio-vocabularies/issues/188

class VocabularyCF(BaseCF):
    """Vocabulary custom field.

    Supporting common vocabulary structure.
    """

    type = "vocabulary"

    def __init__(self, name, vocabulary_id):
        """Constructor."""
        self.vocabulary_id = vocabulary_id
        super().__init__(name)

    @property
    def mapping(self):
        """Return the mapping."""
        # FIXME: can objects be done with ES objects
        # deal with compatibility between versions (e.g. keyword changes name)
        _mapping = {
            "type": "object",
            "properties": {
                "@v": {"type": "keyword"},
                "id": {"type": "keyword"},
                "title": {"type": "object", "dynamic": True},
            },
        }

        return _mapping

    def schema(self):
        """Marshmallow schema for vocabulary custom fields."""
        return fields.Mapping()

    def options(self):
        """."""
        return [
            {"text": "Zacharias Zacharodimos", "value": "zzacharo"},
            {"text": "Pablo Panero", "value": "ppanero"},
        ]
