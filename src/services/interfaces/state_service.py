"""State service interface for Redis-based backtest state management."""

from typing import Protocol, Dict, Any, Optional


class IStateService(Protocol):
    """Interface for backtest state management using Redis.

    The state service manages volatile state during backtest execution,
    separate from persistent database storage.
    """

    def create_backtest(
        self,
        backtest_id: str,
        config: Dict[str, Any]
    ) -> bool:
        """Create a new backtest record in Redis.

        Args:
            backtest_id: Unique backtest identifier
            config: Backtest configuration

        Returns:
            True if successful, False otherwise
        """
        ...

    def update_status(
        self,
        backtest_id: str,
        status: str,
        progress: Optional[float] = None,
        current_time: Optional[str] = None,
        result: Any = None,
        error: Optional[str] = None
    ) -> bool:
        """Update backtest status in Redis.

        Args:
            backtest_id: Backtest identifier
            status: New status (pending/running/completed/failed)
            progress: Progress percentage (0-100)
            current_time: Current simulation time
            result: Result data (will be JSON serialized)
            error: Error message if failed

        Returns:
            True if successful, False otherwise
        """
        ...

    def get_backtest(
        self,
        backtest_id: str,
        default: Any = None,
        restore_dataframe: bool = False
    ) -> Optional[Dict[str, Any]]:
        """Get backtest record from Redis.

        Args:
            backtest_id: Backtest identifier
            default: Default value if not found
            restore_dataframe: Whether to restore DataFrame objects

        Returns:
            Backtest data or default if not found
        """
        ...

    def delete_backtest(self, backtest_id: str) -> bool:
        """Delete backtest record from Redis.

        Args:
            backtest_id: Backtest identifier

        Returns:
            True if deleted, False otherwise
        """
        ...

    def list_backtests(self, limit: int = 50) -> list:
        """List all backtest records from Redis.

        Args:
            limit: Maximum number of results

        Returns:
            List of backtest IDs and status
        """
        ...
