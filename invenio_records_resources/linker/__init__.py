# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
# Copyright (C) 2020 Northwestern University.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Link factory used to generate URLs inside records."""

from .base import Linker
from .builders import DeleteLinkBuilder, FilesLinkBuilder, LinkBuilder, \
    SearchLinkBuilder, SelfLinkBuilder
