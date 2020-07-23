# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2020 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Persistent identifier manager."""

from invenio_pidstore import current_pidstore
from invenio_pidstore.models import PIDStatus
from invenio_pidstore.resolver import Resolver
from invenio_pidstore.providers.recordid_v2 import RecordIdProviderV2
from invenio_records.api import Record

class PIDManager:

    def __init__(self, resolver_cls=Resolver, resolver_obj_getter=Record.get_record,
                 resolver_pid_type="recid", minter_pid_type="recid_v2",
                 provider_cls=RecordIdProviderV2, object_type='rec',
                 registered_only=True):

        self.resolver = resolver_cls(
            pid_type=resolver_pid_type,
            getter=resolver_obj_getter,
            registered_only=registered_only
        )
        self.provider_cls = provider_cls
        self.object_type=object_type

    @property
    def minter():
        # Need to be lazy loaded to be on an app ctx
        return current_pidstore.minters[minter_pid_type]

    @property
    def fetcher():
        return current_pidstore.fetchers[resolver_pid_type]

    def create(self, record, status=PIDStatus.REGISTERED,
               options=None, **kwargs):
        self.provider_cls.default_status_with_obj = status

        return self.provider_cls.create(
            self.object_type, record.id, options, **kwargs
        ).pid

    def get(self, value):
        return fetcher.get(value)

    def resolve(self, id_):
        return self.resolver.resolve(id_)
