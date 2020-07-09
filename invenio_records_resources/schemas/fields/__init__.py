#
# Copyright (C) 2020 CERN.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Custom marshmallow fields."""

from .persistent_identifier import PersistentIdentifier
from .sanitized_unicode import SanitizedUnicode

__all__ = ("PersistentIdentifier", "SanitizedUnicode")
