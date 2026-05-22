# SPDX-FileCopyrightText: 2022 CERN.
# SPDX-License-Identifier: MIT

"""Test Base Custom Field."""

import pytest

from invenio_records_resources.services.custom_fields import BaseCF


def test_basecf_abstract():
    """Cant simply instantiate."""
    with pytest.raises(TypeError):
        cf = BaseCF("name", "myorg")
