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
from luqum.tree import Phrase, Word
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

    def map_word(self, node, **kwargs):
        """Modify a word node."""
        return self._word_fun(node) if self._word_fun else node

    def map_phrase(self, node, **kwargs):
        """Modify a phrase node."""
        return self._phrase_fun(node) if self._phrase_fun else node


class RestrictedTerm:
    """Class used to apply specific permissions to search.

    ex. "internal_notes.note": RestrictedTerm(system_access_permission)
    restricts the internal_notes.note field from being searched by anyone else
    than system process
    """

    def __init__(self, permission):
        """Constructor."""
        self.permission = permission

    def allows(self, identity):
        """Check the permission for the whole term."""
        return self.permission.allows(identity)


class RestrictedTermValue:
    """Class used to apply specific permissions to search specific words.

    ex. "_exists_": RestrictedTermValue(
            system_access_permission, word=word_internal_notes
        ),
    will rewrite the searched field based on given permission
    """

    def __init__(self, permission, word=None, phrase=None):
        """Constructor."""
        self.permission = permission
        self._word_fun = word
        self._phrase_fun = phrase

    def map_word(self, node, context, **kwargs):
        """Modify a word node."""
        is_restricted = not self.permission.allows(context["identity"])
        if not is_restricted:
            return node
        if self._word_fun and is_restricted:
            return self._word_fun(node)
        else:
            return Word("")

    def map_phrase(self, node, context, **kwargs):
        """Modify a phrase node."""
        is_restricted = not self.permission.allows(context["identity"])
        if not is_restricted:
            return node
        if self._phrase_fun and is_restricted:
            return self._phrase_fun(node)
        else:
            return Phrase("")


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

        # TODO if you need another if clause here, please refactor
        if isinstance(term_name, FieldValueMapper):
            field_value_mapper = term_name
            term_name = field_value_mapper.term_name
        if isinstance(term_name, RestrictedTermValue):
            field_value_mapper = term_name
            term_name = node.name
        if isinstance(term_name, RestrictedTerm):
            allows = term_name.allows(context["identity"])
            term_name = node.name
            # field_value_mapper is left as None on purpose - if the permission
            # allows, we don't map any query, we allow it "as is"
            if not allows:
                raise QuerystringValidationError(
                    _("Invalid search field: %(field_name)s.", field_name=node.name)
                )
        # If a allow list exists, the term must be allowed to be queried.
        if self._allow_list and term_name not in self._allow_list:
            raise QuerystringValidationError(
                _("Invalid search field: %(field_name)s.", field_name=node.name)
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
        yield node if mapper is None else mapper.map_word(node, context=context)

    def visit_phrase(self, node, context):
        """Visit a phrase term."""
        mapper = context.get("field_value_mapper")
        yield node if mapper is None else mapper.map_phrase(node, context=context)
