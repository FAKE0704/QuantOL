"""Backtest task persistence service for database operations.

This service handles CRUD operations for backtest tasks stored in the database,
providing persistent storage separate from Redis state management.
"""

import json
import pandas as pd
from datetime import datetime
from typing import Optional, List, Dict, Any
from src.support.log.logger import logger
from src.database import get_db_adapter
from src.utils.async_helpers import retry_on_locked
from src.utils.encoders import QuantOLEncoder, to_json_string


class BacktestTaskService:
    """Service for managing backtest tasks in the database."""

    # Maximum number of completed backtests to keep per user
    MAX_COMPLETED_BACKTESTS = 5

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
        try:
            db = get_db_adapter()

            # Convert config to JSON string
            config_json = json.dumps(config)

            async with db.pool as conn:
                await conn.execute("""
                    INSERT INTO BacktestTasks
                    (backtest_id, user_id, name, status, config, log_file_path, created_at)
                    VALUES (?, ?, ?, 'pending', ?, ?, CURRENT_TIMESTAMP)
                """, backtest_id, user_id, name or f"Backtest {backtest_id}", config_json, log_file_path or "")

            logger.info(f"Created backtest task {backtest_id} for user {user_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to create backtest task: {e}")
            return False

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
        try:
            db = get_db_adapter()

            # Build update query dynamically
            updates = []
            params = []
            param_count = 1

            if status is not None:
                updates.append(f"status = ${param_count}")
                params.append(status)
                param_count += 1

                # Update timestamps based on status
                # Use CURRENT_TIMESTAMP (works in both SQLite and PostgreSQL)
                if status == "running":
                    updates.append(f"started_at = CURRENT_TIMESTAMP")
                elif status in ("completed", "failed"):
                    updates.append(f"completed_at = CURRENT_TIMESTAMP")

            if progress is not None:
                updates.append(f"progress = ${param_count}")
                params.append(progress)
                param_count += 1

            if current_time is not None:
                updates.append(f"current_time = ${param_count}")
                params.append(current_time)
                param_count += 1

            if result_summary is not None:
                updates.append(f"result_summary = ${param_count}")
                # Use QuantOLEncoder to handle Timestamp, DataFrame, Series, numpy types
                params.append(json.dumps(result_summary, cls=QuantOLEncoder))
                param_count += 1

            if error_message is not None:
                updates.append(f"error_message = ${param_count}")
                params.append(error_message)
                param_count += 1

            if not updates:
                return True  # Nothing to update

            # Add backtest_id to params
            params.append(backtest_id)

            query = f"""
                UPDATE BacktestTasks
                SET {', '.join(updates)}
                WHERE backtest_id = ${param_count}
            """

            # Execute with retry on database lock
            async def execute_update():
                async with db.pool as conn:
                    await conn.execute(query, *params)

            await retry_on_locked(execute_update, max_retries=3, delay=0.1)

            logger.debug(f"Updated backtest task {backtest_id}")
            return True

        except Exception as e:
            error_str = str(e).lower()
            # Only log as error if it's not a lock issue (retries already handled)
            if 'locked' not in error_str and 'database is locked' not in error_str:
                logger.error(f"Failed to update backtest task: {e}")
            else:
                logger.warning(f"Failed to update backtest task after retries: {e}")
            return False

    async def get_backtest_task(self, backtest_id: str) -> Optional[Dict[str, Any]]:
        """Get a single backtest task by ID.

        Args:
            backtest_id: Backtest identifier

        Returns:
            Task data or None if not found
        """
        try:
            db = get_db_adapter()

            async with db.pool as conn:
                row = await conn.fetchrow("""
                    SELECT id, backtest_id, user_id, name, status, progress,
                           current_time, config, result_summary, error_message,
                           log_file_path, created_at, started_at, completed_at
                    FROM BacktestTasks
                    WHERE backtest_id = $1
                """, backtest_id)

                if not row:
                    return None

                return self._row_to_dict(row)

        except Exception as e:
            logger.error(f"Failed to get backtest task: {e}")
            return None

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
        try:
            db = get_db_adapter()

            query = """
                SELECT id, backtest_id, user_id, name, status, progress,
                       current_time, config, result_summary, error_message,
                       log_file_path, created_at, started_at, completed_at
                FROM BacktestTasks
                WHERE user_id = $1
            """
            params = [user_id]

            if status:
                query += " AND status = $2"
                params.append(status)

            query += " ORDER BY created_at DESC LIMIT $3"
            params.append(limit)

            async with db.pool as conn:
                rows = await conn.fetch(query, *params)

                return [self._row_to_dict(row) for row in rows]

        except Exception as e:
            logger.error(f"Failed to list user backtests: {e}")
            return []

    async def delete_backtest_task(self, backtest_id: str, user_id: int) -> bool:
        """Delete a backtest task.

        Args:
            backtest_id: Backtest identifier
            user_id: User ID (for authorization)

        Returns:
            True if deleted, False otherwise
        """
        try:
            db = get_db_adapter()

            async with db.pool as conn:
                cursor = await conn.execute(
                    "DELETE FROM BacktestTasks WHERE backtest_id = ? AND user_id = ?",
                    backtest_id, user_id
                )

                # Check if any rows were deleted using cursor.rowcount
                rows_deleted = cursor.rowcount if cursor else 0
                return rows_deleted > 0

        except Exception as e:
            logger.error(f"Failed to delete backtest task: {e}")
            return False

    async def delete_backtest(self, backtest_id: str) -> bool:
        """Delete a backtest by ID (without user check).

        Args:
            backtest_id: Backtest identifier

        Returns:
            True if deleted, False otherwise
        """
        try:
            db = get_db_adapter()

            async with db.pool as conn:
                cursor = await conn.execute(
                    "DELETE FROM BacktestTasks WHERE backtest_id = ?",
                    backtest_id
                )

                # Check if any rows were deleted using cursor.rowcount
                rows_deleted = cursor.rowcount if cursor else 0
                return rows_deleted > 0

        except Exception as e:
            logger.error(f"Failed to delete backtest: {e}")
            return False

    async def cleanup_old_backtests(self, user_id: int) -> bool:
        """Clean up old completed backtests, keeping only the most recent ones.

        Args:
            user_id: User ID

        Returns:
            True if successful, False otherwise
        """
        try:
            db = get_db_adapter()

            async with db.pool as conn:
                # Count completed backtests
                count = await conn.fetchval("""
                    SELECT COUNT(*) FROM BacktestTasks
                    WHERE user_id = ? AND status = 'completed'
                """, user_id)

                if count <= self.MAX_COMPLETED_BACKTESTS:
                    return True  # No cleanup needed

                # Delete oldest completed backtests beyond the limit
                await conn.execute("""
                    DELETE FROM BacktestTasks
                    WHERE id IN (
                        SELECT id FROM BacktestTasks
                        WHERE user_id = ? AND status = 'completed'
                        ORDER BY created_at ASC
                        LIMIT ?
                    )
                """, user_id, count - self.MAX_COMPLETED_BACKTESTS)

                logger.info(f"Cleaned up {count - self.MAX_COMPLETED_BACKTESTS} old backtests for user {user_id}")
                return True

        except Exception as e:
            logger.error(f"Failed to cleanup old backtests: {e}")
            return False

    def _row_to_dict(self, row) -> Dict[str, Any]:
        """Convert database row to dictionary."""
        # Helper to safely parse JSON
        def safe_json_loads(val):
            if not val or val == "":
                return {}
            try:
                return json.loads(val)
            except:
                return {}

        # Helper to format datetime (handles both datetime objects and SQLite strings)
        def format_datetime(val):
            if not val:
                return None
            if isinstance(val, str):
                return val
            return val.isoformat()

        return {
            "id": row["id"],
            "backtest_id": row["backtest_id"],
            "user_id": row["user_id"],
            "name": row["name"],
            "status": row["status"],
            "progress": float(row["progress"]) if row["progress"] is not None else 0.0,
            "current_time": row["current_time"],
            "config": safe_json_loads(row["config"]),
            "result_summary": safe_json_loads(row["result_summary"]),
            "error_message": row["error_message"],
            "log_file_path": row["log_file_path"],
            "created_at": format_datetime(row["created_at"]),
            "started_at": format_datetime(row["started_at"]),
            "completed_at": format_datetime(row["completed_at"]),
        }


# Global singleton
backtest_task_service = BacktestTaskService()
