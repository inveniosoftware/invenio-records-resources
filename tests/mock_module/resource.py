"""Example resource."""

from uritemplate import URITemplate

from invenio_records_resources.resources import RecordResource, \
    RecordResourceConfig


class ResourceConfig(RecordResourceConfig):
    """Mock service configuration."""

    item_route = '/mocks/<pid_value>'
    list_route = '/mocks'

    links_config = {
        'record': {
            'self': URITemplate('/mocks{/pid_value}'),
        }
    }


class Resource(RecordResource):
    """Mock service."""

    default_config = ResourceConfig
