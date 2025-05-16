# -*- coding: utf-8 -*-
#
# Copyright (C) 2021-2024 CERN.
# Copyright (C) 2025 CESNET.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
"""Transfer registry."""


class TransferRegistry:
    """A registry for transfer providers."""

    def __init__(self, default_transfer_type: str):
        """Creates a new transfer registry.

        :param default_transfer_type: The default transfer type to use when no transfer type is provided in file upload initiation.
        """
        self._transfers = {}
        self._default_transfer_type = default_transfer_type

    @property
    def default_transfer_type(self):
        """Get the default transfer type."""
        return self._default_transfer_type

    def register(self, transfer_cls):
        """Register a new transfer provider."""
        transfer_type = transfer_cls.transfer_type

        if transfer_type in self._transfers:
            raise RuntimeError(
                f"Transfer with type '{transfer_type}' " "is already registered."
            )

        self._transfers[transfer_type] = transfer_cls

    def get_transfer_class(self, transfer_type):
        """Get transfer class by transfer type."""
        return self._transfers[transfer_type]

    def get_transfer_types(self):
        """Get all registered transfer types."""
        return self._transfers.keys()

    def get_transfer(
        self,
        *,
        record,
        file_service,
        key=None,
        transfer_type=None,
        file_record=None,
        uow=None,
    ):
        """Get transfer for the given record and file service.

        To specify the file that the transfer should be performed on,
        either the file record or the key together with transfer_type
        must be provided.
        """
        if file_record is not None:
            key = file_record.key
            transfer_type = file_record.transfer.transfer_type
        if key is None:
            raise ValueError("Either key or file_record must be provided.")
        if transfer_type is None:
            raise ValueError("Either file_record or transfer_type must be provided.")

        return self._transfers[transfer_type](
            record=record,
            key=key,
            file_service=file_service,
            file_record=file_record,
            uow=uow,
        )
