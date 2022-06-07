# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
#
# Invenio-Records-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Records Models."""

from invenio_db import db
from invenio_files_rest.models import ObjectVersion
from sqlalchemy.dialects import mysql
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy_utils.types import UUIDType


class FileRecordModelMixin:
    """Base class for a record file, storing its state and metadata."""

    __record_model_cls__ = None
    """Record model to be for the ``record_id`` foreign key."""

    key = db.Column(
        db.Text().with_variant(mysql.VARCHAR(255), "mysql"),
        nullable=False,
    )
    """Filename key (can be path-like also)."""

    @declared_attr
    def record_id(cls):
        """Record ID foreign key."""
        return db.Column(
            UUIDType,
            db.ForeignKey(cls.__record_model_cls__.id, ondelete="RESTRICT"),
            nullable=False,
        )

    @declared_attr
    def record(cls):
        """Record the file belnogs to."""
        return db.relationship(cls.__record_model_cls__)

    @declared_attr
    def object_version_id(cls):
        """Object version ID foreign key."""
        return db.Column(
            UUIDType,
            db.ForeignKey(ObjectVersion.version_id, ondelete="RESTRICT"),
            nullable=True,
        )

    @declared_attr
    def object_version(cls):
        """Object version connected to the record file."""
        return db.relationship(ObjectVersion)

    @declared_attr
    def __table_args__(cls):
        """Table args."""
        return (
            db.Index(
                f"uidx_{cls.__tablename__}_id_key",
                "id",
                "key",
                unique=True,
            ),
        )
