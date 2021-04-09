# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
# Copyright (C) 2020 Northwestern University.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Record Service API."""

from ..base import ServiceConfig
from ..records.links import RecordLink
from .links import FileLink
from .results import FileItem, FileList
from .schema import FileSchema


#
# Configurations
#
class FileServiceConfig(ServiceConfig):
    """File Service configuration."""

    record_cls = None

    permission_action_prefix = ""

    file_result_item_cls = FileItem
    file_result_list_cls = FileList

    file_schema = FileSchema

    file_links_list = {
        "self": RecordLink("{+api}/records/{id}/files"),
    }

    file_links_item = {
        "self": FileLink("{+api}/records/{id}/files/{key}"),
        "content": FileLink("{+api}/records/{id}/files/{key}/content"),
    }
