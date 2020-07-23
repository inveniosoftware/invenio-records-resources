# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2020 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Record module."""

from .pid_manager import PIDManager
from .pid_record import PIDRecord


__all__ = ("PIDManager", "PIDRecord")
