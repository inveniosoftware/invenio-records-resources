# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
# Copyright (C) 2020 Northwestern University.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Common errors utilities."""


def _iter_errors_dict(message_node, fieldpath=""):
    """Recursively yield validation error dicts.

    :params dict|list|value: Marshmallow error node (first is a dict)

    For example:
    {
        'metadata': {
            'creators': {
                0: {
                    'type': [
                        "Invalid value. Choose one of
                        ['organizational', 'personal']."
                    ]
                }
            }
        }
    }
    :fieldpath string: path to current message_node
    :returns dict:

    Example validation error dicts returned:
    {
        "field": "metadata.creators.0.type",
        "messages": [
            "Invalid value. Choose one of ['organizational', 'personal']."
        ]
    }
    """
    if isinstance(message_node, dict):
        for field, child in message_node.items():
            yield from _iter_errors_dict(
                child, fieldpath=(f"{fieldpath}." if fieldpath else "") + f"{field}"
            )
    elif isinstance(message_node, list):
        # If the node is a list, it's a leaf node of messages
        yield {"field": f"{fieldpath}", "messages": message_node}
    else:
        # leaf node - always wrap in a list
        yield {"field": f"{fieldpath}", "messages": [message_node]}


def validation_error_to_list_errors(exception):
    """Convert exception to a list of error dicts.

    Each error dict is shaped as follows:

        {
            "field": "dotted.path.to.field",
            "messages": ["errors msg1", ... "error msgN"]
        }

    :params ValidationError exception: Marshmallow load errror
    :returns: list<dict>
    """
    errors = exception.normalized_messages()
    return list(_iter_errors_dict(errors))
