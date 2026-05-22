#!/usr/bin/env bash
# SPDX-FileCopyrightText: 2020 CERN.
# SPDX-FileCopyrightText: 2022-2023 Graz University of Technology.
# SPDX-License-Identifier: MIT

# Usage:
#   ./run-tests.sh [pytest options and args...]
#
# Note: the DB, SEARCH and CACHE services to use are determined by corresponding environment
#       variables if they are set -- otherwise, the following defaults are used:
#       DB=postgresql, SEARCH=elasticsearch and CACHE=redis
#
# Example for using mysql instead of postgresql:
#    DB=mysql CACHE=redis ./run-tests.sh

# Quit on errors
set -o errexit

# Quit on unbound symbols
set -o nounset

# Always bring down docker services
function cleanup() {
    eval "$(docker-services-cli down --env)"
}
trap cleanup EXIT

python -m check_manifest
python -m setup extract_messages --output-file /dev/null
python -m sphinx.cmd.build -qnNW docs docs/_build/html
eval "$(docker-services-cli up --db ${DB:-postgresql} --search ${SEARCH:-opensearch} --cache ${CACHE:-redis} --s3 ${S3BACKEND:-minio} --env)"

python -m pytest $@

python -m sphinx.cmd.build -qnNW -b doctest docs docs/_build/doctest
