# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 CERN.
#
# Invenio-RDM-Records is free software; you can redistribute it and/or modify
# it under the terms of the MIT License; see LICENSE file for more details.

"""Custom Fields for InvenioRDM."""

import calendar

from arrow import Arrow
from babel_edtf import parse_edtf
from edtf.parser.edtf_exceptions import EDTFParseException
from marshmallow import fields
from marshmallow_utils.fields import EDTFDateTimeString, ISODateString
from pytz import utc

from .base import BaseListCF, ensure_no_field_cls
from .mappings import EDTFMapping, ISODateMapping


class ISODateStringCF(BaseListCF):
    """ISO date custom field."""

    @ensure_no_field_cls
    def __init__(self, name, **kwargs):
        """Constructor."""
        super().__init__(name, field_cls=ISODateString, **kwargs)

    @property
    def mapping(self):
        """Return the mapping."""
        return ISODateMapping().to_dict()


class EDTFDateStringCF(BaseListCF):
    """EDTF date custom field."""

    @ensure_no_field_cls
    def __init__(self, name, **kwargs):
        """Constructor."""
        super().__init__(name, field_cls=EDTFDateTimeString, **kwargs)

    @property
    def mapping(self):
        """Return the mapping."""
        return EDTFMapping().to_dict()

    @property
    def field(self):
        """Marshmallow field custom fields."""
        _schema = self._field_cls(**self._field_args)
        if self._multiple:
            return fields.List(_schema)
        return _schema

    @classmethod
    def _format_date(cls, date):
        """Format the given date into ISO format."""
        arrow = Arrow.fromtimestamp(calendar.timegm(date), tzinfo=utc)
        return arrow.date().isoformat()

    @classmethod
    def _calculate_date_range(cls, date):
        pd = parse_edtf(date)
        return {
            "date": date,
            "date_range": {
                "gte": cls._format_date(pd.lower_strict()),
                "lte": cls._format_date(pd.upper_strict()),
            },
        }

    def dump(self, data, cf_key="custom_fields"):
        """Dump the custom field.

        Gets both the record and the custom fields key as parameters.
        This supports the case where a field is based on others, both
        custom and non-custom fields.
        """
        dates = data[cf_key].get(self.name)
        if dates:
            try:
                if self._multiple:
                    for date in dates:
                        data[cf_key][self.name] = self._calculate_date_range(date)
                else:
                    # dates is just one date
                    data[cf_key][self.name] = self._calculate_date_range(dates)
            except EDTFParseException:
                pass

    def load(self, record, cf_key="custom_fields"):
        """Load the custom field.

        Gets both the record and the custom fields key as parameters.
        This supports the case where a field is based on others, both
        custom and non-custom fields.
        """
        date = record.get(cf_key, {}).pop(self.name, None)
        if date:
            record[cf_key][self.name] = date["date"]
