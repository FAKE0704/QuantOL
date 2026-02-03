"""Task service interface for backtest CRUD operations."""

from typing import Protocol, Dict, Any, List, Optional


class ITaskService(Protocol):
    """Interface for backtest task CRUD operations.

    The task service manages persistent storage of backtest tasks
    in the database, separate from Redis state management.
    """

    async def create_backtest_task(
        self,
        backtest_id: str,
        user_id: int,
        config: Dict[str, Any],
        name: Optional[str] = None,
        log_file_path: Optional[str] = None,
    ) -> bool:
        """Create a new backtest task record.

        Args:
            backtest_id: Unique backtest identifier
            user_id: User ID who owns the backtest
            config: Backtest configuration (will be stored as JSON)
            name: Optional backtest name
            log_file_path: Optional path to log file

        Returns:
            True if successful, False otherwise
        """
        ...

    async def update_backtest_task(
        self,
        backtest_id: str,
        status: Optional[str] = None,
        progress: Optional[float] = None,
        current_time: Optional[str] = None,
        result_summary: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None,
    ) -> bool:
        """Update backtest task status and progress.

        Args:
            backtest_id: Backtest identifier
            status: New status (pending/running/completed/failed)
            progress: Progress percentage (0-100)
            current_time: Current simulation time
            result_summary: Results summary (will be stored as JSON)
            error_message: Error message if failed

        Returns:
            True if successful, False otherwise
        """
        ...

    async def get_backtest_task(self, backtest_id: str) -> Optional[Dict[str, Any]]:
        """Get a single backtest task by ID.

        Args:
            backtest_id: Backtest identifier

        Returns:
            Task data or None if not found
        """
        ...

    async def list_user_backtests(
        self,
        user_id: int,
        status: Optional[str] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """List backtests for a user.

        Args:
            user_id: User ID
            status: Optional status filter
            limit: Maximum number of results

        Returns:
            List of backtest tasks
        """
        ...

    async def delete_backtest_task(self, backtest_id: str, user_id: int) -> bool:
        """Delete a backtest task.

        Args:
            backtest_id: Backtest identifier
            user_id: User ID (for authorization)

        Returns:
            True if deleted, False otherwise
        """
        ...

    async def cleanup_old_backtests(self, user_id: int) -> bool:
        """Clean up old completed backtests.

        Keeps only the most recent ones based on MAX_COMPLETED_BACKTESTS.

        Args:
            user_id: User ID

        Returns:
            True if successful, False otherwise
        """
        ...
