# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Query interpreter API."""

from elasticsearch_dsl import Q
from flask import current_app

from ..errors import InvalidQueryError


def _default_parser(querystring=None):
    """Default parser that uses the Q() from elasticsearch_dsl."""
    if querystring:
        return Q("query_string", query=querystring)
    return Q()


class QueryInterpreter:
    """Query interpreter."""

    def __init__(self, query_parser=None, **kwargs):
        """Constructor."""
        self.query_parser = query_parser or _default_parser
        self.params = kwargs

    def parse(self, querystring):
        """Parse a querystring."""
        try:
            return self.query_parser(querystring)
        except SyntaxError:
            current_app.logger.debug(
                "Failed parsing query: {0}".format(querystring),
                exc_info=True
            )
            raise InvalidQueryError()
