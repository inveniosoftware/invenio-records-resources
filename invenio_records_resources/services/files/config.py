# -*- coding: utf-8 -*-
#
# Copyright (C) 2020-2022 CERN.
# Copyright (C) 2020-2025 Northwestern University.
# Copyright (C) 2025 CESNET i.a.l.e.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Record Service API."""

from ..base import ServiceConfig
from .components import (
    FileContentComponent,
    FileMetadataComponent,
    FileMultipartContentComponent,
    FileProcessorComponent,
)
from .extractors import ZipExtractor
from .processors import ImageMetadataExtractor, ZipProcessor
from .processors.zip import ZipProcessor
from .results import ContainerItemResult, ContainerListResult, FileItem, FileList
from .schema import FileSchema


#
# Configurations
#
class FileServiceConfig(ServiceConfig):
    """File Service configuration."""

    service_id = "files"

    record_cls = None

    permission_action_prefix = ""

    file_result_item_cls = FileItem
    file_result_list_cls = FileList
    file_result_container_list_cls = ContainerListResult
    file_result_container_item_cls = ContainerItemResult

    file_schema = FileSchema

    max_files_count = 100

    # Inheriting service config should define these
    file_links_list = {}
    file_links_item = {}
    container_item_links_item = {}

    # At the resource level and link serialization (service) level
    allow_upload = True
    allow_archive_download = True

    components = [
        FileMetadataComponent,
        FileContentComponent,
        FileMultipartContentComponent,
        FileProcessorComponent,
    ]

    file_processors = [
        ImageMetadataExtractor(),
        ZipProcessor(),
    ]

    file_extractors = [ZipExtractor()]
