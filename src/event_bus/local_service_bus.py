"""In-memory event bus for service-to-service communication.

This is a simpler, synchronous event bus for local service communication,
separate from the Redis-based event bus used for distributed events.
"""

from typing import Callable, Dict, List, Any
from collections import defaultdict

from src.event_bus import EventBus
from src.support.log.logger import logger


class LocalServiceBus(EventBus):
    """In-memory event bus for local service communication.

    This bus:
    - Maintains subscriber lists in memory
    - Dispatches events synchronously
    - Is suitable for single-process service communication
    - Avoids circular dependencies by decoupling publishers and subscribers
    """

    def __init__(self):
        self._subscribers: Dict[str, List[Callable[[Any], Any]]] = defaultdict(list)

    def publish(self, event_type: str, event: Any) -> None:
        """Publish an event to all subscribers.

        Args:
            event_type: Type/category of event
            event: Event object to publish
        """
        if event_type not in self._subscribers:
            logger.debug(f"No subscribers for event type: {event_type}")
            return

        for handler in self._subscribers[event_type]:
            try:
                handler(event)
            except Exception as e:
                logger.error(f"Error in event handler for {event_type}: {e}")

    def subscribe(self, event_type: str, handler: Callable[[Any], Any]) -> None:
        """Subscribe to events of a specific type.

        Args:
            event_type: Type/category of event to subscribe to
            handler: Callable to handle events
        """
        if handler not in self._subscribers[event_type]:
            self._subscribers[event_type].append(handler)
            logger.debug(f"Subscribed handler to event type: {event_type}")

    def unsubscribe(self, event_type: str, handler: Callable[[Any], Any]) -> None:
        """Unsubscribe a handler from an event type.

        Args:
            event_type: Type/category of event
            handler: Handler to remove
        """
        if handler in self._subscribers[event_type]:
            self._subscribers[event_type].remove(handler)
            logger.debug(f"Unsubscribed handler from event type: {event_type}")

    def clear_subscribers(self, event_type: str = None) -> None:
        """Clear subscribers. Useful for testing.

        Args:
            event_type: Specific event type to clear, or None to clear all
        """
        if event_type:
            self._subscribers[event_type].clear()
        else:
            self._subscribers.clear()
