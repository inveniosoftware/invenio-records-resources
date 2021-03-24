# -*- coding: utf-8 -*-
#
# Copyright (C) 2020-2021 CERN.
# Copyright (C) 2020-2021 Northwestern University.
#
# Flask-Resources is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Utility for rendering URI template links."""

from ..base import Link


class FileLink(Link):
    """Short cut for writing record links."""

    @staticmethod
    def vars(file_record, vars):
        """Variables for the URI template."""
        vars.update({
            "key": file_record.key,
        })
