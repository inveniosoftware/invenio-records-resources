#!/usr/bin/env sh
# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
#
# Invenio-Resources is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

pydocstyle invenio_resources tests docs && \
isort invenio_resources tests --check-only --diff && \
check-manifest --ignore ".travis-*" && \
sphinx-build -qnNW docs docs/_build/html && \
python setup.py test
