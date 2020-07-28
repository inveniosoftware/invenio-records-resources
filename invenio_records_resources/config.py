# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
# Copyright (C) 2020 Northwestern University.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Invenio Resources module to create REST APIs."""

from elasticsearch import VERSION as ES_VERSION

lt_es7 = ES_VERSION[0] < 7

PIDSTORE_RECID_FIELD = "recid"

# TODO: Might be something to place with the fundamental invenio config
SERVER_HOSTNAME = "localhost:5000"
