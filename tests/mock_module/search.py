"""Example search."""

from invenio_search import RecordsSearch as RecordsSearchBase


class RecordsSearch(RecordsSearchBase):
    """Records search class."""

    class Meta:
        """Configuration."""

        # TODO: should be 'records' but apparently the alias is not created.
        index = 'records-record-v1.0.0'
