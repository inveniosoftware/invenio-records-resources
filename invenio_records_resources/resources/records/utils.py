# SPDX-FileCopyrightText: 2020-2021 CERN.
# SPDX-FileCopyrightText: 2020-2021 Northwestern University.
# SPDX-License-Identifier: MIT

"""Invenio Resources module to create REST APIs."""

import hashlib

from flask import request


def search_preference():
    """Generating an identifier for use with the search engine preference param."""
    user_agent = request.headers.get("User-Agent", "")
    ip = request.remote_addr
    user_hash = f"{ip}-{user_agent}".encode("utf8")
    alg = hashlib.md5()
    alg.update(user_hash)
    return alg.hexdigest()
