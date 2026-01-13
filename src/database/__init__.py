"""Database module for QuantOL.

Exports the database adapter factory function.
"""

from src.core.data.database_factory import get_db_adapter

__all__ = ["get_db_adapter"]
