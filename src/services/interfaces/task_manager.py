"""Task manager interface for backtest orchestration."""

from typing import Protocol, Any
from fastapi import BackgroundTasks


class ITaskManager(Protocol):
    """Interface for backtest task orchestration.

    The task manager is responsible for:
    - Submitting backtest tasks for async execution
    - Managing the execution lifecycle
    - Coordinating between state service, task service, and WebSocket manager
    """

    async def submit_backtest(
        self,
        backtest_id: str,
        request: Any,
        background_tasks: BackgroundTasks,
        user_id: int = 1
    ) -> None:
        """Submit a backtest for async execution.

        This method:
        1. Creates a backtest record in Redis (via state service)
        2. Creates a backtest task record in database (via task service)
        3. Submits the task for background execution

        Args:
            backtest_id: Unique identifier for the backtest
            request: Backtest request object with configuration
            background_tasks: FastAPI background tasks
            user_id: User ID who owns the backtest
        """
        ...
