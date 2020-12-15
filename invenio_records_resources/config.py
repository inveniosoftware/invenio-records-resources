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

SITE_HOSTNAME = "localhost:5000"


class ConfigLoaderMixin:
    """Mixin for supporting configuration loading and overwriting."""

    default_config = None
    """Default service configuration."""

    config_name = None
    """Name of Flask configuration variable.

    The variable is used to dynamically load a service configuration specified
    by the user. A concrete service subclass most overwrite this attribute.
    """

    def load_config(self, config):
        """Load a configuration.

        Uses ``config`` if not None. Otherwise the method will try to load
        the config from a Flask configuration variable (named using the
        ``config_name`` attribute). Last it will use the config provided in
        ``default_config``.

        :param config: A service configuration or None.
        """
        return config or self.default_config
