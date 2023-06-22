# -*- coding: utf-8 -*-
#
# Copyright (C) 2020-2022 CERN.
# Copyright (C) 2021 Northwestern University.
# Copyright (C) 2023 Graz University of Technology.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Records service component base classes."""

from ...base.components import BaseServiceComponent


class ServiceComponent(BaseServiceComponent):
    """Base service component."""

    def create(self, identity, **kwargs):
        """Create handler."""
        pass

    def read(self, identity, **kwargs):
        """Read handler."""
        pass

    def update(self, identity, **kwargs):
        """Update handler."""
        pass

    def delete(self, identity, **kwargs):
        """Delete handler."""
        pass

    def search(self, identity, search, params, **kwargs):
        """Search handler."""
        return search


class BaseRecordFilesComponent(ServiceComponent):
    _files_attr_key = None
    _files_data_key = None
    _files_bucket_attr_key = None
    _files_bucket_id_attr_key = None

    @property
    def files_attr_key(self):
        return self._files_attr_key

    @property
    def files_data_key(self):
        return self._files_data_key or self._files_attr_key

    @property
    def files_bucket_attr_key(self):
        return self._files_bucket_attr_key

    @property
    def files_bucket_id_attr_key(self):
        return self._files_bucket_id_attr_key

    def get_record_files(self, record):
        return getattr(record, self.files_attr_key)

    def get_record_bucket(self, record):
        return getattr(record, self._files_bucket_attr_key)

    def get_record_bucket_id(self, record):
        return getattr(record, self._files_bucket_attr_key)
