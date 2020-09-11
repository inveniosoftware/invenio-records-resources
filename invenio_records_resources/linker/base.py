# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
# Copyright (C) 2020 Northwestern University.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Link factory that generate all the links for a given namespace."""


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
