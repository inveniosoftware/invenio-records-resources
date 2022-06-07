# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 CERN.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Files processor component."""

from ....proxies import current_service_registry
from ....tasks import extract_file_metadata
from ...uow import TaskOp
from ..processors import ProcessorRunner
from .base import FileServiceComponent


class FileProcessorComponent(FileServiceComponent):
    """File metadata service component."""

    def commit_file(self, identity, id, file_key, record):
        """Post commit file handler."""
        # Ship off a task to extract file metadata once a file is committed.
        service_id = current_service_registry.get_service_id(self.service)
        self.uow.register(TaskOp(extract_file_metadata, service_id, id, file_key))

    def extract_file_metadata(self, identity, id_, file_key, record, file_record):
        """Extract and save file metadata for a given file."""
        if file_record.metadata is None:
            file_record.metadata = {}

        ProcessorRunner(self.service.config.file_processors).run(file_record)
