"""Example search."""

from elasticsearch_dsl import Q
from invenio_search import RecordsSearch as RecordsSearchBase


def terms_filter(field):
    """Create a term filter.

    :param field: Field name.
    :returns: Function that returns the Terms query.
    """
    def inner(values):
        return Q('terms', **{field: values})
    return inner


class RecordsSearch(RecordsSearchBase):
    """Records search class."""

    class Meta:
        """Configuration."""

        # TODO: should be 'records' but apparently the alias is not created.
        index = 'records-record-v1.0.0'
