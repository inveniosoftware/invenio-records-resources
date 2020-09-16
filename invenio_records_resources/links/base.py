# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
# Copyright (C) 2020 Northwestern University.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Link factory that generate all the links for a given namespace."""

from collections import defaultdict

from marshmallow import fields, missing

from .urlutils import base_url


class Linker:
    """Linker class.

    Generates all the links for a given namespace.
    """

    def __init__(self, link_builders):
        """Constructor.

        :param link_builders: dict(string, list<LinkBuilder>)
        """
        self.link_builders = link_builders

    def links(self, namespace, identity, **kwargs):
        """Returns dict of links."""
        output_links = {}
        for link_builder in self.link_builders[namespace]:
            link = link_builder.route_to_link(identity, **kwargs)
            output_links.update(link)
        return output_links

    def register_link_builders(self, link_builders):
        """Updates the internal link_builders with new ones."""
        self.link_builders.update(link_builders)


class LinkStore:
    """Utility class for keeping track of links.

    The ``config`` argument is a dictionary with link namespaces as keys and a
    dictionary of link types and their URITemplate objects.

    Exmple usage:

    ..code-block:: python

        link_store = LinkStore()
        data = {
            'links': {
                'self': {'pid_value': '12345'},
                'draft': {'pid_value': '12345'},
            },
        }
        link_store.add('record', data['links'])
        link_store.resolve(config={
            'record': {
                'self': URITemplate('/api/records{/pid_value}'),
                'draft': URITemplate('/api/records{/pid_value}/draft'),
            }
        })
    """

    def __init__(self, config=None):
        """Constructor."""
        self.config = config
        self._links = defaultdict(list)

    def add(self, namespace, links):
        """Adds a dictionary of links under a namespace."""
        self._links[namespace].append(links)

    def resolve(self, context=None, config=None):
        """Resolves in-place all the tracked link dictionaries."""
        config = config or self.config
        assert config, "Links config is empty."
        context = context or {}
        for ns, link_objects in self._links.items():
            if ns not in config:
                raise Exception(f'Unknown links namespace: {ns}')
            for links in link_objects:
                for k, v in links.items():
                    links[k] = base_url(
                        path=config[ns][k].expand(**context, **v),
                        # TODO: how do we handle this via URITemplate?
                        # querystring='...',
                    )


class LinksField(fields.Field):
    """Links field."""

    # NOTE: forces serialization
    _CHECK_ATTRIBUTE = False

    def __init__(self, links_schema=None, namespace=None, **kwargs):
        """Constructor."""
        self.links_schema = links_schema
        self.namespace = namespace
        super().__init__(**kwargs)

    def _serialize(self, value, attr, obj, *args, **kwargs):
        # NOTE: We pass the full parent `obj`, since we want to make it
        # available to the links schema
        result = self.links_schema(context=self.context).dump(obj)
        self.context['links_store'].add(self.namespace, result)
        return result

    def _deserialize(self, value, attr, data, **kwargs):
        # NOTE: we don't deserialize the links, and we don't use dump_only=True
        # because that will by default raise a validation error unless you have
        # configured marshmallow to exclude unknown values.
        return missing
