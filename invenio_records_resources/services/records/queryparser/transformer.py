# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 CERN.
# Copyright (C) 2023 Graz University of Technology.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Query tree transformer.

See https://luqum.readthedocs.io/en/latest/quick_start.html#manipulating for
how to build your own query tree transformer.
"""

from functools import partial

from invenio_i18n import gettext as _
from luqum.visitor import TreeTransformer

from invenio_records_resources.services.errors import QuerystringValidationError


class SearchFieldTransformer(TreeTransformer):
    """Transform from user-friendly field names to internal field names."""

    def __init__(self, mapping, *args, **kwargs):
        """Constructor."""
        self._mapping = mapping
        super().__init__(self, *args, **kwargs)

    @classmethod
    def factory(cls, mapping=None):
        """Create a new field transformer."""
        return partial(cls, mapping or {})

    def visit_search_field(self, node, context):
        """Visit a search field."""
        if node.name not in self._mapping:
            raise QuerystringValidationError(
                _("Invalid search field: {field_name}.").format(field_name=node.name)
            )
        else:
            new_node = node.clone_item()
            new_node.name = self._mapping[node.name]
            new_node.children = list(self.clone_children(node, new_node, context))
            yield new_node
