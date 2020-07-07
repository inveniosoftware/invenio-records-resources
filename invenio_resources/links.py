# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
#
# Invenio-Resources is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Invenio Resources module to create REST APIs."""

from flask import current_app

from .config import LINK_URLS


def _base_url(api=False):
    """Creates the base URL for API and UI endpoints."""
    url = "{}/api" if api else "{}"
    return url.format(current_app.config['SERVER_HOSTNAME'])


def link_for(api, tpl, **kwargs):
    """Create a link using specific template."""
    tpl = LINK_URLS.get(tpl)

    return tpl.format(base=_base_url(api), **kwargs)


def search_links(url_args, total):
    """Create search query links."""
    api_base = link_for(api=True, tpl='records')  # Search links are api only
    links = {
        'self': api_base,
    }

    if url_args:
        pagination = url_args.pop('pagination')  # Assumes it is always there
        links['self'] = "{}?page={}".format(
            api_base,
            pagination["links"]["self"]["page"],
        )
        url_args.pop('page') # Remove since it is not needed

        if pagination['from_idx'] >= 1:
            links['prev'] = "{}?page={}".format(
                pagination["links"]["prev"]["page"],
                api_base
            )
        # FIXME: < min(total, self.max_result_window) How access max_res_win
        if pagination['to_idx'] < total:
            links['next'] = "{}?page={}".format(
                pagination["links"]["next"]["page"],
                api_base
            )

        for key, link in links.items():
            for arg, value in url_args.items():
                links[key] = "{link}&{arg}={value}".format(
                    link=link, arg=arg, value=value
                )

    return links
