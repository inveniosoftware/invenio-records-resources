# -*- coding: utf-8 -*-
#
# Copyright (C) 2024 TU Wien.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Service component for detecting file types."""

from ...uow import TaskOp
from ..tasks import detect_file_type
from .base import FileServiceComponent


class FileTypeDetectionComponent(FileServiceComponent):
    """Service component for detecting file types."""

    def commit_file(self, identity, id, file_key, record):
        """Detect the file format as soon as the file has been committed."""
        self.uow.register(TaskOp(detect_file_type, str(record.bucket.id), file_key))
