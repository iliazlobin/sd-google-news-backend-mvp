"""Conditional array type: PostgreSQL ARRAY, SQLite JSON."""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy import TypeDecorator


class StringArray(TypeDecorator):
    """Store list[str] as ARRAY(Text) on PostgreSQL, JSON on SQLite.

    Selection is automatic based on the engine dialect at DDL-compile time.
    """
    impl = sa.JSON
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(sa.ARRAY(sa.Text))
        return dialect.type_descriptor(sa.JSON)

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if dialect.name == "postgresql":
            return list(value) if isinstance(value, list) else value
        return list(value) if isinstance(value, list) else value

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        if dialect.name == "postgresql":
            return list(value)
        return list(value) if isinstance(value, list) else value
