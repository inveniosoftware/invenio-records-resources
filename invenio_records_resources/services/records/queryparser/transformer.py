# -*- coding: utf-8 -*-
#
# Copyright (C) 2022-2024 CERN.
# Copyright (C) 2023 Graz University of Technology.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Query tree transformer.

See https://luqum.readthedocs.io/en/latest/quick_start.html#manipulating for
how to build your own query tree transformer.
"""

from invenio_i18n import gettext as _
from luqum.visitor import TreeTransformer

from invenio_records_resources.services.errors import QuerystringValidationError


class FieldValueMapper:
    """Class used to remap values to new terms."""

    def __init__(self, term_name, word=None, phrase=None):
        """Initialize field value mapper."""
        self._term_name = term_name
        self._word_fun = word
        self._phrase_fun = phrase

    @property
    def term_name(self):
        """Get the term name."""
        return self._term_name

    def map_word(self, node):
        """Modify a word node."""
        return self._word_fun(node) if self._word_fun else node

    def map_phrase(self, node):
        """Modify a phrase node."""
        return self._phrase_fun(node) if self._phrase_fun else node


class SearchFieldTransformer(TreeTransformer):
    """Transform from user-friendly field names to internal field names."""

    def __init__(self, mapping, allow_list, *args, **kwargs):
        """Constructor."""
        self._mapping = mapping
        self._allow_list = allow_list
        super().__init__(*args, **kwargs)

    def visit_search_field(self, node, context):
        """Visit a search field."""
        # Use the node name if not mapped for transformation.
        term_name = self._mapping.get(node.name, node.name)
        field_value_mapper = None

        if isinstance(term_name, FieldValueMapper):
            field_value_mapper = term_name
            term_name = field_value_mapper.term_name

        # If a allow list exists, the term must be allowed to be queried.
        if self._allow_list and not term_name in self._allow_list:
            raise QuerystringValidationError(
                _("Invalid search field: {field_name}.").format(field_name=node.name)
            )

        if field_value_mapper:
            context["field_value_mapper"] = field_value_mapper

        # Returns a copy of the node.
        new_node = node.clone_item()
        new_node.name = term_name
        new_node.children = list(self.clone_children(node, new_node, context))
        yield new_node

    def visit_word(self, node, context):
        """Visit a word term."""
        mapper = context.get("field_value_mapper")
        yield node if mapper is None else mapper.map_word(node)

    def visit_phrase(self, node, context):
        """Visit a phrase term."""
        mapper = context.get("field_value_mapper")
        yield node if mapper is None else mapper.map_phrase(node)
