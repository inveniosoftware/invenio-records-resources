"""Example search."""

from elasticsearch_dsl import Q


def terms_filter(field):
    """Create a term filter used for aggregations.

    :param field: Field name.
    :returns: Function that returns the Terms query.
    """
    def inner(values):
        return Q('terms', **{field: values})
    return inner
