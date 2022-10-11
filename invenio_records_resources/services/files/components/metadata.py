# -*- coding: utf-8 -*-
#
# Copyright (C) 2021-2022 CERN.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Files metadata component components."""

from copy import deepcopy

from ..schema import InitFileSchema
from ..transfer import Transfer
from .base import FileServiceComponent


class FileMetadataComponent(FileServiceComponent):
    """File metadata service component."""

    def init_files(self, identity, id, record, data):
        """Init files handler."""
        schema = InitFileSchema(many=True)
        validated_data = schema.load(data)
        for file_metadata in validated_data:
            temporary_obj = deepcopy(file_metadata)
            file_type = temporary_obj.pop("storage_class", None)
            transfer = Transfer.get_transfer(
                file_type, service=self.service, uow=self.uow
            )
            _ = transfer.init_file(record, temporary_obj)

    def update_file_metadata(self, identity, id, file_key, record, data):
        """Update file metadata handler."""
        # FIXME: move this call to a transfer call
        record.files.update(file_key, data=data)

    # TODO: `commit_file` might vary based on your storage backend (e.g. S3)
    def commit_file(self, identity, id, file_key, record):
        """Commit file handler."""
        Transfer.commit_file(record, file_key)
