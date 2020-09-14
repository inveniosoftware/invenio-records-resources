"""Example resource."""

from invenio_records_resources.resources import RecordResource, \
    RecordResourceConfig


class ResourceConfig(RecordResourceConfig):
    """Mock service configuration."""

    item_route = '/mocks/<pid_value>'
    list_route = '/mocks'


class Resource(RecordResource):
    """Mock service."""

    default_config = ResourceConfig
