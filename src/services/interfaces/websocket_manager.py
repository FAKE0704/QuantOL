"""WebSocket manager interface for real-time progress updates."""

from typing import Protocol, Dict, Set
from fastapi import WebSocket


class IWebSocketManager(Protocol):
    """Interface for WebSocket connection management.

    The WebSocket manager handles real-time communication
    for backtest progress updates to connected clients.
    """

    async def connect(self, websocket: WebSocket, backtest_id: str) -> None:
        """Connect WebSocket and subscribe to backtest progress.

        Args:
            websocket: WebSocket connection
            backtest_id: Backtest identifier to subscribe to
        """
        ...

    def disconnect(self, websocket: WebSocket, backtest_id: str) -> None:
        """Disconnect WebSocket connection.

        Args:
            websocket: WebSocket connection
            backtest_id: Backtest identifier
        """
        ...

    async def broadcast_progress(
        self,
        backtest_id: str,
        data: dict
    ) -> None:
        """Broadcast progress update to all subscribers.

        Args:
            backtest_id: Backtest identifier
            data: Progress data to broadcast
        """
        ...

    async def send_personal_message(
        self,
        message: dict,
        websocket: WebSocket
    ) -> None:
        """Send message to a single connection.

        Args:
            message: Message data
            websocket: WebSocket connection
        """
        ...
