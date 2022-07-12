# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 CERN.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Test Base Custom Field."""

import pytest

from invenio_records_resources.services.custom_fields import BaseCF


def test_basecf_abstract():
    """Cant simply instantiate."""
    with pytest.raises(TypeError):
        cf = BaseCF("name", "myorg")
