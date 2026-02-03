"""Service interface definitions for dependency injection and testing."""

from .task_manager import ITaskManager
from .task_service import ITaskService
from .state_service import IStateService
from .websocket_manager import IWebSocketManager

__all__ = [
    "ITaskManager",
    "ITaskService",
    "IStateService",
    "IWebSocketManager",
]
