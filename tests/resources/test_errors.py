# SPDX-FileCopyrightText: 2026 Paradigm Repositories.
# SPDX-License-Identifier: MIT

"""Resource error handling tests."""

import pytest
from invenio_search.engine import search

from invenio_records_resources.resources.errors import HTTPJSONSearchRequestError


def _request_error(info):
    """Create a search engine RequestError with the given error info."""
    return search.exceptions.RequestError(400, "search_error", info)


def _log_records(caplog):
    return [
        r
        for r in caplog.records
        if "Unhandled search engine RequestError" in r.getMessage()
    ]


def test_mapped_cause_is_not_logged(base_app, caplog):
    """A mapped root cause keeps its response and stays silent."""
    error = _request_error(
        {
            "error": {
                "root_cause": [
                    {"type": "query_parsing_exception", "reason": "bad query"}
                ]
            }
        }
    )

    with base_app.app_context():
        exc = HTTPJSONSearchRequestError(error)

    assert exc.code == 400
    assert exc.errors is None
    assert not _log_records(caplog)


def test_unmapped_cause_is_logged_and_exposed(base_app, caplog):
    """An unmapped root cause is logged and its type exposed to the client."""
    error = _request_error(
        {
            "error": {
                "root_cause": [
                    {
                        "type": "mapper_parsing_exception",
                        "reason": "failed to parse field [foo]",
                    }
                ]
            }
        }
    )

    with base_app.app_context():
        exc = HTTPJSONSearchRequestError(error)

    assert exc.code == 500
    assert exc.errors == [{"type": "mapper_parsing_exception"}]

    log_records = _log_records(caplog)
    assert len(log_records) == 1
    assert "failed to parse field [foo]" in log_records[0].getMessage()


@pytest.mark.parametrize(
    "info",
    [
        "not-a-dict",
        {},
        {"error": {}},
        {"error": {"root_cause": []}},
    ],
)
def test_malformed_error_info_does_not_raise(base_app, caplog, info):
    """Malformed error info still results in a logged generic 500."""
    error = _request_error(info)

    with base_app.app_context():
        exc = HTTPJSONSearchRequestError(error)

    assert exc.code == 500
    assert exc.errors is None
    assert len(_log_records(caplog)) == 1
