"""Example service."""

from invenio_records_resources.services import RecordService, \
    RecordServiceConfig

from .api import Record
from .permissions import PermissionPolicy
from .schema import RecordSchema
from .search import terms_filter


class ServiceConfig(RecordServiceConfig):
    """Mock service configuration."""

    permission_policy_cls = PermissionPolicy
    record_cls = Record
    schema = RecordSchema
    search_facets_options = {
        'aggs': {
            'type': {
                'terms': {'field': 'metadata.type.type'},
                'aggs': {
                    'subtype': {
                        'terms': {'field': 'metadata.type.subtype'},
                    }
                }
            }
        },
        'post_filters': {
            'subtype': terms_filter('metadata.type.subtype'),
            'type': terms_filter('metadata.type.type'),
        }
    }


class Service(RecordService):
    """Mock service."""

    default_config = ServiceConfig
