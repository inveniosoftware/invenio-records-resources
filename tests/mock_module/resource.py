"""Example resource."""

from uritemplate import URITemplate

from invenio_records_resources.resources import RecordResource, \
    RecordResourceConfig


class ResourceConfig(RecordResourceConfig):
    """Mock service configuration."""

    list_route = "/mocks"
    item_route = f"{list_route}/<pid_value>"

    links_config = {
        "record": {
            "self": URITemplate(f"{list_route}{{/pid_value}}"),
        },
        "search": {
            "self": URITemplate(f"{list_route}{{?params*}}"),
            "prev": URITemplate(f"{list_route}{{?params*}}"),
            "next": URITemplate(f"{list_route}{{?params*}}"),
        }
    }


class Resource(RecordResource):
    """Mock service."""

    default_config = ResourceConfig
