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

SITE_UI_URL = "https://127.0.0.1:5000"

SITE_API_URL = "https://127.0.0.1:5000/api"
