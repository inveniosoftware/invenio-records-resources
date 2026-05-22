# SPDX-FileCopyrightText: 2020 CERN.
# SPDX-License-Identifier: MIT

"""Files request body parser."""

from flask import request


class RequestStreamParser:
    """Parse the request body."""

    def parse(self):
        """Parse the request body."""
        return {
            "request_stream": request.stream,
            "request_content_length": request.content_length,
        }
