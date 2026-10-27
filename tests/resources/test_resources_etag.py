# SPDX-FileCopyrightText: 2020 CERN.
# SPDX-FileCopyrightText: 2020 Northwestern University.
# SPDX-FileCopyrightText: 2026 RERO.
# SPDX-License-Identifier: MIT

"""Resources etag test."""

import json

import pytest

#: Templates for the ``If-Match`` values a client may legitimately send: the
#: bare revision id accepted so far, the strong entity-tag the response
#: carries, and the weak tag a proxy leaves behind after recompressing it.
ENTITY_TAG_FORMS = ["{}", '"{}"', 'W/"{}"']
ENTITY_TAG_IDS = ["bare-integer", "strong-tag", "weak-tag"]


@pytest.fixture()
def input_data(client, headers):
    """Input data (as coming from the view layer)."""
    data = {
        "metadata": {"title": "Test"},
    }
    res = client.post("/mocks", headers=headers, data=json.dumps(data))
    assert res.status_code == 201
    return res.json


def test_etag_update(app, client, input_data, headers):
    """Test a simple REST API flow."""
    id_ = input_data["id"]
    revision_id = input_data["revision_id"]

    # Update with outdated etag version
    res = client.put(
        f"/mocks/{id_}",
        headers={**headers, "if_match": 100},
        data=json.dumps(input_data),
    )
    assert res.status_code == 412

    # Update with correct etag version
    res = client.put(
        f"/mocks/{id_}",
        headers={**headers, "if_match": revision_id},
        data=json.dumps(input_data),
    )
    assert res.status_code == 200


def test_etag_delete(app, client, input_data, headers):
    """Test a simple REST API flow."""
    id_ = input_data["id"]
    revision_id = input_data["revision_id"]

    # Delete with outdated etag version
    res = client.delete(f"/mocks/{id_}", headers={**headers, "if_match": 100})
    assert res.status_code == 412

    # Delete with correct etag version
    res = client.delete(f"/mocks/{id_}", headers={**headers, "if_match": revision_id})
    assert res.status_code == 204


def test_etag_update_round_trip(app, client, input_data, headers):
    """Echo back the ETag of a response, unaltered, as the If-Match of an update.

    This is the exchange the REST API documentation prescribes, and the one a
    conformant HTTP client performs on its own: the value sent is the value
    received, never a hand-stripped revision id.
    """
    id_ = input_data["id"]

    res = client.get(f"/mocks/{id_}", headers=headers)
    assert res.status_code == 200
    etag = res.headers["ETag"]
    assert etag == '"{}"'.format(input_data["revision_id"])

    res = client.put(
        f"/mocks/{id_}",
        headers={**headers, "If-Match": etag},
        data=json.dumps(input_data),
    )
    assert res.status_code == 200


def test_etag_delete_round_trip(app, client, input_data, headers):
    """Echo back the ETag of a response, unaltered, as the If-Match of a delete."""
    id_ = input_data["id"]

    res = client.get(f"/mocks/{id_}", headers=headers)
    assert res.status_code == 200
    etag = res.headers["ETag"]

    res = client.delete(f"/mocks/{id_}", headers={**headers, "If-Match": etag})
    assert res.status_code == 204


@pytest.mark.parametrize("tag_form", ENTITY_TAG_FORMS, ids=ENTITY_TAG_IDS)
def test_etag_update_entity_tag_forms(app, client, input_data, headers, tag_form):
    """Update accepts the revision id bare, as a strong tag and as a weak tag."""
    id_ = input_data["id"]
    if_match = tag_form.format(input_data["revision_id"])

    res = client.put(
        f"/mocks/{id_}",
        headers={**headers, "If-Match": if_match},
        data=json.dumps(input_data),
    )
    assert res.status_code == 200


@pytest.mark.parametrize("tag_form", ENTITY_TAG_FORMS, ids=ENTITY_TAG_IDS)
def test_etag_delete_entity_tag_forms(app, client, input_data, headers, tag_form):
    """Delete accepts the revision id bare, as a strong tag and as a weak tag."""
    id_ = input_data["id"]
    if_match = tag_form.format(input_data["revision_id"])

    res = client.delete(f"/mocks/{id_}", headers={**headers, "If-Match": if_match})
    assert res.status_code == 204


@pytest.mark.parametrize("tag_form", ENTITY_TAG_FORMS, ids=ENTITY_TAG_IDS)
def test_etag_update_outdated_entity_tag_forms(
    app, client, input_data, headers, tag_form
):
    """An outdated revision id is a precondition failure in every accepted form."""
    id_ = input_data["id"]

    res = client.put(
        f"/mocks/{id_}",
        headers={**headers, "If-Match": tag_form.format(100)},
        data=json.dumps(input_data),
    )
    assert res.status_code == 412


@pytest.mark.parametrize(
    "if_match",
    [
        '"abc"',  # a syntactically valid tag, but not a revision id
        "*",  # the wildcard: out of scope, rejected as before
        '"5", "7"',  # a list of tags: out of scope, rejected as before
    ],
    ids=["non-numeric-tag", "wildcard", "tag-list"],
)
def test_etag_update_invalid_if_match(app, client, input_data, headers, if_match):
    """An If-Match that is not a single numeric entity-tag is a validation error."""
    id_ = input_data["id"]

    res = client.put(
        f"/mocks/{id_}",
        headers={**headers, "If-Match": if_match},
        data=json.dumps(input_data),
    )
    assert res.status_code == 400
    assert res.json["message"] == "A validation error occurred."
    assert res.json["errors"] == [
        {"field": "if_match", "messages": ["Not a valid integer."]}
    ]
