#!/usr/bin/env bash
# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

# Quit on errors
set -o errexit

# Quit on unbound symbols
set -o nounset

# Always bring down docker services
function cleanup() {
    docker-services-cli down
}

trap cleanup EXIT

python -m check_manifest --ignore ".*-requirements.txt"
python -m sphinx.cmd.build -qnNW docs docs/_build/html
docker-services-cli up es postgresql redis
python -m pytest
tests_exit_code=$?
exit "$tests_exit_code"
