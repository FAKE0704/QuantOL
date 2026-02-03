"""Service-level events for inter-service communication.

Defines events for:
- Backtest status changes
- Progress updates
- Task lifecycle events
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any
from src.event_bus.event_types import BaseEvent


@dataclass
class BacktestStatusChangedEvent(BaseEvent):
    """Event fired when backtest status changes."""
    backtest_id: str
    old_status: Optional[str]
    new_status: str
    progress: float
    user_id: int
    timestamp: datetime
    error_message: Optional[str] = None
    current_time: Optional[str] = None
    result_summary: Optional[Dict[str, Any]] = None


@dataclass
class BacktestProgressEvent(BaseEvent):
    """Event fired for backtest progress updates."""
    backtest_id: str
    progress: float
    current_time: str
    timestamp: datetime


@dataclass
class BacktestCreatedEvent(BaseEvent):
    """Event fired when a new backtest is created."""
    backtest_id: str
    user_id: int
    config: Dict[str, Any]
    timestamp: datetime


@dataclass
class BacktestCompletedEvent(BaseEvent):
    """Event fired when a backtest completes."""
    backtest_id: str
    user_id: int
    result_summary: Dict[str, Any]
    timestamp: datetime
