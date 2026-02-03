"""Event coordinator for backtest engine.

This coordinator manages event-driven communication between components,
extracting from BacktestEngine's event handling methods.
"""

from typing import Callable, Dict, List, Any, Type
from collections import deque
from src.support.log.logger import logger


class EventCoordinator:
    """Event coordination service for backtest engine.

    Manages event queue registration, dispatching, and processing.
    Extracted from BacktestEngine event handling methods.
    """

    def __init__(self):
        """Initialize event coordinator."""
        self._queue: deque = deque()
        self._handlers: Dict[Type, Callable] = {}
        self._logger = logger.getChild('EventCoordinator')

    def register_handler(self, event_type: Type, handler: Callable) -> None:
        """Register an event handler for a specific event type.

        Args:
            event_type: Event class to handle (e.g., StrategySignalEvent)
            handler: Callable function to handle the event
        """
        self._handlers[event_type] = handler
        self._logger.debug(f"Registered handler for {event_type.__name__}")

    def push_event(self, event: Any) -> None:
        """Push an event to the queue.

        Args:
            event: Event object to queue
        """
        self._queue.append(event)

    def process_event_queue(self) -> None:
        """Process all pending events in the queue.

        Events are dispatched to their registered handlers in order.
        """
        while self._queue:
            event = self._queue.popleft()
            event_type = type(event)

            handler = self._handlers.get(event_type)
            if handler:
                try:
                    handler(event)
                except Exception as e:
                    self._logger.error(
                        f"Error processing {event_type.__name__}: {e}"
                    )
            else:
                self._logger.warning(f"No handler registered for {event_type.__name__}")

    def clear_queue(self) -> None:
        """Clear all pending events from the queue."""
        self._queue.clear()
        self._logger.debug("Event queue cleared")

    def get_queue_size(self) -> int:
        """Get current queue size.

        Returns:
            Number of events in queue
        """
        return len(self._queue)

    def get_registered_handlers(self) -> List[Type]:
        """Get list of registered event types.

        Returns:
            List of event type classes
        """
        return list(self._handlers.keys())
