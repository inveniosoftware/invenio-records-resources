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

    def __init__(self, mapping, allow_list, *args, **kwargs):
        """Constructor."""
        self._mapping = mapping
        self._allow_list = allow_list
        super().__init__(self, *args, **kwargs)

    def visit_search_field(self, node, context):
        """Visit a search field."""
        # Use the node name if not mapped for transformation.
        term_name = self._mapping.get(node.name, node.name)

        # If a allow list exists, the term must be allowed to be queried.
        if self._allow_list and not term_name in self._allow_list:
            raise QuerystringValidationError(
                _("Invalid search field: {field_name}.").format(field_name=node.name)
            )

        # Returns a copy of the node.
        new_node = node.clone_item()
        new_node.name = term_name
        new_node.children = list(self.clone_children(node, new_node, context))
        yield new_node
