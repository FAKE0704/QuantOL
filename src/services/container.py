"""Dependency Injection Container for service management.

This container:
- Manages service lifecycle (singleton, transient)
- Resolves dependencies automatically
- Provides backward-compatible global accessors during transition
"""

from typing import Dict, Type, TypeVar, Optional, Callable, Any
from enum import Enum
from src.support.log.logger import logger

T = TypeVar('T')


class ServiceLifetime(Enum):
    """Service lifecycle options."""
    SINGLETON = "singleton"  # One instance for entire application
    TRANSIENT = "transient"  # New instance each time
    SCOPED = "scoped"        # One instance per scope (e.g., per request)


class ServiceContainer:
    """Simple dependency injection container."""

    def __init__(self):
        self._services: Dict[Type, Any] = {}
        self._factories: Dict[Type, Callable[[], Any]] = {}
        self._lifetimes: Dict[Type, ServiceLifetime] = {}
        self._instances: Dict[Type, Any] = {}

    def register(
        self,
        interface: Type[T],
        implementation: Optional[Type[T]] = None,
        factory: Optional[Callable[[], T]] = None,
        lifetime: ServiceLifetime = ServiceLifetime.SINGLETON
    ) -> None:
        """Register a service in the container.

        Args:
            interface: Interface/protocol type
            implementation: Concrete implementation class
            factory: Factory function to create instances
            lifetime: Service lifecycle
        """
        if factory:
            self._factories[interface] = factory
            self._lifetimes[interface] = lifetime
        elif implementation:
            self._services[interface] = implementation
            self._lifetimes[interface] = lifetime
        else:
            raise ValueError("Must provide either implementation or factory")

        logger.debug(f"Registered {interface.__name__} with lifetime {lifetime.value}")

    def resolve(self, interface: Type[T]) -> T:
        """Resolve a service from the container.

        Args:
            interface: Interface/protocol type to resolve

        Returns:
            Service instance

        Raises:
            KeyError: If service not registered
        """
        # Check if already instantiated (for singletons)
        if interface in self._instances:
            return self._instances[interface]

        # Get factory or implementation
        if interface in self._factories:
            factory = self._factories[interface]
            instance = factory()
        elif interface in self._services:
            implementation = self._services[interface]
            instance = implementation()
        else:
            raise KeyError(f"Service not registered: {interface.__name__}")

        # Store singleton instances
        if self._lifetimes.get(interface) == ServiceLifetime.SINGLETON:
            self._instances[interface] = instance

        return instance

    def clear(self) -> None:
        """Clear all singleton instances. Useful for testing."""
        self._instances.clear()


# Global container instance
_container = ServiceContainer()


def get_container() -> ServiceContainer:
    """Get the global service container."""
    return _container


def initialize_services() -> None:
    """Initialize all services and register them in the container.

    This function is called during application startup to:
    1. Create service instances
    2. Register them in the container
    3. Set up event subscriptions

    After calling this, services can be resolved via container.resolve()
    """
    from src.services.backtest_state_service import BacktestStateService
    from src.services.backtest_task_service import BacktestTaskService
    from src.services.websocket_manager import WebSocketManager
    from src.services.backtest_task_manager import BacktestTaskManager

    # Note: We'll register concrete implementations, not interfaces
    # This allows gradual migration from singletons to DI

    # These are already singletons in the codebase
    # We register them for future flexibility
    _container.register(
        BacktestStateService,
        factory=lambda: BacktestStateService(),
        lifetime=ServiceLifetime.SINGLETON
    )
    _container.register(
        BacktestTaskService,
        factory=lambda: BacktestTaskService(),
        lifetime=ServiceLifetime.SINGLETON
    )
    _container.register(
        WebSocketManager,
        factory=lambda: WebSocketManager(),
        lifetime=ServiceLifetime.SINGLETON
    )
    _container.register(
        BacktestTaskManager,
        factory=lambda: BacktestTaskManager(),
        lifetime=ServiceLifetime.SINGLETON
    )

    logger.info("Services initialized and registered in container")
