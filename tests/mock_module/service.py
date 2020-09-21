"""Example service."""

from invenio_records_resources.records.resolver import UUIDResolver
from invenio_records_resources.services import RecordService, \
    RecordServiceConfig
from invenio_records_resources.services.records.params import FacetsParam, \
    SortParam

from .api import Record
from .permissions import PermissionPolicy
from .schema import RecordSchema
from .search import RecordsSearch, terms_filter


class ServiceConfig(RecordServiceConfig):
    """Mock service configuration."""

    permission_policy_cls = PermissionPolicy
    record_cls = Record
    schema = RecordSchema
    search_cls = RecordsSearch
    search_sort_default = 'bestmatch'
    search_sort_default_no_query = 'mostrecent'
    search_sort_options = dict(
        bestmatch=dict(
            title='Best match',
            fields=['_score'],
        ),
        mostrecent=dict(
            title='Most recent',
            fields=['-created'],
        ),
    )
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
    search_params_interpreters_cls = [
        SortParam,
        FacetsParam
    ]

class Service(RecordService):
    """Mock service."""

    default_config = ServiceConfig
