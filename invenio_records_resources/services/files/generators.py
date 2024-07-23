# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 CERN.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""File permissions generators."""
from typing import Dict, List, Union

from invenio_records_permissions.generators import Generator


class IfTransferType(Generator):
    def __init__(
        self,
        transfer_type_to_needs: Dict[str, Union[Generator, List[Generator]]],
        else_: Union[Generator, List[Generator]] = None,
    ):
        # convert to dict of lists if not already
        self._transfer_type_to_needs = {
            transfer_type: needs if isinstance(needs, (list, tuple)) else [needs]
            for transfer_type, needs in transfer_type_to_needs.items()
        }

        if not else_:
            else_ = []
        elif not isinstance(else_, (list, tuple)):
            else_ = [else_]

        self._else = else_

    def needs(self, **kwargs):
        """Enabling Needs."""
        record = kwargs["record"]
        file_key = kwargs.get("file_key")
        if not file_key:
            return []  # no needs if file has not been passed
        file_record = record.files.get(file_key)
        if file_record is None:
            return []

        transfer_type = file_record.transfer.transfer_type
        assert transfer_type is not None, "Transfer type not set on file record"

        if transfer_type not in self._transfer_type_to_needs:
            needs_generators = self._else
        else:
            needs_generators = self._transfer_type_to_needs[transfer_type]

        return [need for x in needs_generators for need in x.needs(**kwargs)]
