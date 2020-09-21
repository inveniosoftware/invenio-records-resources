"""Example resource."""

from uritemplate import URITemplate

from invenio_records_resources.resources import RecordResource, \
    RecordResourceConfig


class ResourceConfig(RecordResourceConfig):
    """Mock service configuration."""

    list_route = "/mocks"
    item_route = f"{list_route}/<pid_value>"

    # IDEA: Formalize the concept of thunk in our codebase and use it
    # TODO: Changing list_route / item_route shouldn't require redefining these
    links_config = {
        "record": {
            "self": URITemplate(f"/api{list_route}{{/pid_value}}"),
        },
        "search": {
            "self": URITemplate(f"/api{list_route}{{?params*}}"),
            "prev": URITemplate(f"/api{list_route}{{?params*}}"),
            "next": URITemplate(f"/api{list_route}{{?params*}}"),
        }
    }


class Resource(RecordResource):
    """Mock service."""

    default_config = ResourceConfig
