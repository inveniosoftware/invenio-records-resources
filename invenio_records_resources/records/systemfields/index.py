# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
# Copyright (C) 2020 Northwestern University.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Index field."""

from elasticsearch_dsl import Index
from invenio_records.systemfields import SystemField
from invenio_search import current_search_client


class IndexField(SystemField):
    """Index field."""

    def __init__(self, index_or_alias, search_alias=None):
        """Initialize the IndexField.

        :param index_or_alias: An index instance or name of index/alias.
        :param search_alias: Name of alias to use for searches.
        """
        if isinstance(index_or_alias, Index):
            self._index = index_or_alias
        else:
            self._index = Index(index_or_alias, using=current_search_client)
        # Set search alias name directly on the index
        self._index.search_alias = search_alias or self._index._name

    #
    # Data descriptor methods (i.e. attribute access)
    #
    def __get__(self, record, owner=None):
        """Get the persistent identifier."""
        return self._index
