# -*- coding: utf-8 -*-
#
# Copyright (C) 2020-2021 CERN.
# Copyright (C) 2020-2021 Northwestern University.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Service tests."""


def assert_expected_links(pid_value, links, site_hostname="127.0.0.1:5000"):
    """Compare generated links to expected links."""
    expected_links = {
        "self": f"https://{site_hostname}/api/mocks/{pid_value}",
        "files": f"https://{site_hostname}/api/mocks/{pid_value}/files",
    }
    assert expected_links == links


def test_create_links(app, client, input_data, headers):
    res = client.post('/mocks', headers=headers, json=input_data)

    assert res.status_code == 201
    pid_value = res.json["id"]
    assert_expected_links(pid_value, res.json["links"])


def test_read_links(app, client, input_data, headers):
    res = client.post('/mocks', headers=headers, json=input_data)
    pid_value = res.json["id"]

    res = client.get(f'/mocks/{pid_value}', headers=headers)

    assert_expected_links(pid_value, res.json["links"])


def test_update_links(app, client, input_data, headers):
    res = client.post('/mocks', headers=headers, json=input_data)
    pid_value = res.json["id"]
    data = res.json
    data['metadata']['title'] = 'New title'

    res = client.put(f'/mocks/{pid_value}', headers=headers, json=data)

    assert res.status_code == 200
    assert_expected_links(pid_value, res.json["links"])
