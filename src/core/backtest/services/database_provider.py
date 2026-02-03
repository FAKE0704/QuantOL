"""Database provider for backtest operations.

This module provides a clean abstraction for database access,
removing hardcoded dependencies and debug print statements.
"""

from typing import Optional, Dict, Any
from src.core.data.database_adapter import DatabaseAdapter
from src.support.log.logger import logger


class BacktestDatabaseProvider:
    """Database provider for backtest operations.

    This class provides a clean abstraction over the database adapter,
    removing hardcoded Streamlit dependencies and debug print statements.
    """

    def __init__(self, db_adapter: Optional[DatabaseAdapter] = None):
        """Initialize database provider.

        Args:
            db_adapter: Optional database adapter. If None, must be set later via set_adapter()
        """
        self._db_adapter = db_adapter
        self._logger = logger.getChild('BacktestDatabaseProvider')

    def set_adapter(self, db_adapter: DatabaseAdapter) -> None:
        """Set the database adapter.

        Args:
            db_adapter: Database adapter instance
        """
        self._db_adapter = db_adapter
        self._logger.debug("Database adapter set")

    @property
    def db(self) -> DatabaseAdapter:
        """Get the database adapter.

        Returns:
            DatabaseAdapter instance

        Raises:
            ValueError: If no database adapter is configured
        """
        if self._db_adapter is not None:
            return self._db_adapter

        raise ValueError(
            "Database adapter not configured. "
            "Please provide db_adapter during initialization or call set_adapter()."
        )

    async def save_order(self, order: Dict[str, Any]) -> str:
        """Save an order to the database.

        Args:
            order: Order data dictionary

        Returns:
            Order ID

        Raises:
            Exception: If save operation fails
        """
        try:
            return await self.db.save_order(order)
        except Exception as e:
            self._logger.error(f"Failed to save order: {e}")
            raise

    async def save_trade(self, trade: Dict[str, Any]) -> bool:
        """Save a trade to the database.

        Args:
            trade: Trade data dictionary

        Returns:
            True if successful

        Raises:
            Exception: If save operation fails
        """
        try:
            return await self.db.save_trade(trade)
        except Exception as e:
            self._logger.error(f"Failed to save trade: {e}")
            raise

    def get_adapter(self) -> Optional[DatabaseAdapter]:
        """Get the underlying database adapter (for legacy code compatibility).

        Returns:
            Database adapter instance or None
        """
        return self._db_adapter
