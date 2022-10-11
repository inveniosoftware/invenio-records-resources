# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 CERN.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""File permissions generators."""


from invenio_access.permissions import any_user, system_process
from invenio_records_permissions.generators import Generator
from invenio_search.engine import dsl

from .transfer import TransferType


class AnyUserIfFileIsLocal(Generator):
    """Allows any user."""

    def needs(self, **kwargs):
        """Enabling Needs."""
        record = kwargs["record"]
        file_key = kwargs.get("file_key")
        is_file_local = True
        if file_key:
            file_record = record.files.get(file_key)
            # file_record __bool__ returns false for `if file_record`
            file = file_record.file if file_record is not None else None
            is_file_local = not file or file.storage_class == TransferType.LOCAL
        else:
            file_records = record.files.entries
            for file_record in file_records:
                file = file_record.file
                if file and file.storage_class != TransferType.LOCAL:
                    is_file_local = False
                    break

        if is_file_local:
            return [any_user]
        else:
            return [system_process]

    def query_filter(self, **kwargs):
        """Match all in search."""
        return dsl.Q("match_all")
