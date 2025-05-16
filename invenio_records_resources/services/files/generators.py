# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 CERN.
# Copyright (C) 2025 CESNET.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""File permissions generators."""

from invenio_records_permissions.generators import ConditionalGenerator


class IfTransferType(ConditionalGenerator):
    """Conditional generator that checks the transfer type of a file."""

    def __init__(
        self,
        transfer_type,
        then_,
        else_=None,
    ):
        """Initializes the generator.

        :param: transfer_type: The transfer type to check for.
        """

        def to_list(value):
            if not value:
                return []
            return value if isinstance(value, (list, tuple)) else [value]

        super().__init__(to_list(then_), to_list(else_))
        self._transfer_type = transfer_type

    def _condition(self, **kwargs):
        """Check if the transfer type of the file is the expected one."""
        # initiating an upload - check if the transfer type is correct
        # in the file metadata
        file_metadata = kwargs.get("file_metadata")
        if file_metadata is not None:
            return (
                file_metadata.get("transfer", {}).get("type", None)
                == self._transfer_type
            )

        # already uploaded and checking access - check if the transfer type is
        # correct in the file record
        record = kwargs["record"]
        file_key = kwargs.get("file_key")
        if not file_key:
            return False
        file_record = record.files.get(file_key)
        if file_record is None:
            return False

        transfer_type = file_record.transfer.transfer_type
        assert transfer_type is not None, "Transfer type not set on file record"

        return transfer_type == self._transfer_type
