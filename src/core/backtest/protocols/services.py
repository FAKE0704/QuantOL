"""Backtest engine service interface definitions.

This module defines the protocol interfaces for backtest engine components,
enabling dependency injection and testability.
"""

from typing import Protocol, Dict, Any, Optional, List, Callable
from datetime import datetime
import pandas as pd


class IDatabaseProvider(Protocol):
    """Database access provider interface.

    Provides an abstraction for database operations used by the backtest engine.
    """

    @property
    def db(self) -> Any:
        """Get the database adapter instance.

        Returns:
            Database adapter instance

        Raises:
            ValueError: If no database adapter is configured
        """
        ...

    async def save_order(self, order: Dict[str, Any]) -> str:
        """Save an order to the database.

        Args:
            order: Order data dictionary

        Returns:
            Order ID or identifier

        Raises:
            Exception: If save operation fails
        """
        ...

    async def save_trade(self, trade: Dict[str, Any]) -> bool:
        """Save a trade to the database.

        Args:
            trade: Trade data dictionary

        Returns:
            True if successful

        Raises:
            Exception: If save operation fails
        """
        ...


class IEquityService(Protocol):
    """Equity tracking service interface.

    Manages equity calculation and tracking throughout backtest execution.
    """

    def update_equity(
        self,
        timestamp: datetime,
        price: float,
        portfolio_data: Optional[Dict[str, Any]] = None
    ) -> None:
        """Update equity record at a specific timestamp.

        Args:
            timestamp: Current timestamp
            price: Current price for equity calculation
            portfolio_data: Optional portfolio position data
        """
        ...

    def get_equity_history(self) -> List[Dict[str, Any]]:
        """Get historical equity records.

        Returns:
            List of equity records with timestamp, price, position, cash, total_value
        """
        ...

    def calculate_max_drawdown(self) -> float:
        """Calculate maximum drawdown from equity history.

        Returns:
            Maximum drawdown as a percentage (0-1)
        """
        ...

    def get_current_equity(self) -> float:
        """Get current total equity value.

        Returns:
            Current equity value
        """
        ...


class IResultsService(Protocol):
    """Results aggregation and metrics calculation service interface.

    Calculates performance metrics and aggregates backtest results.
    """

    def get_results(
        self,
        trades: List[Dict],
        debug_data: Optional[Dict] = None,
        parser_data: Optional[Dict] = None,
        price_data: Optional[pd.DataFrame] = None,
        signals_data: Optional[pd.DataFrame] = None
    ) -> Dict[str, Any]:
        """Aggregate and format backtest results.

        Args:
            trades: List of executed trades
            debug_data: Strategy debug data
            parser_data: Parser data with indicators
            price_data: Price data with signals
            signals_data: Signals data

        Returns:
            Dictionary containing all backtest results and metrics
        """
        ...

    def calculate_advanced_metrics(self, trades: List[Dict]) -> Dict[str, Any]:
        """Calculate advanced performance metrics.

        Args:
            trades: List of trades with profit/loss information

        Returns:
            Dictionary of metrics (sharpe_ratio, win_rate, max_drawdown, etc.)
        """
        ...


class IEventCoordinator(Protocol):
    """Event coordination interface for backtest engine.

    Manages event-driven communication between components.
    """

    def register_handler(self, event_type: type, handler: Callable) -> None:
        """Register an event handler for a specific event type.

        Args:
            event_type: Event class to handle
            handler: Callable function to handle the event
        """
        ...

    def push_event(self, event: Any) -> None:
        """Push an event to the queue.

        Args:
            event: Event object to queue
        """
        ...

    def process_event_queue(self) -> None:
        """Process all pending events in the queue.

        Events are dispatched to their registered handlers in order.
        """
        ...

    def clear_queue(self) -> None:
        """Clear all pending events from the queue."""
        ...


class IOrderCoordinator(Protocol):
    """Order execution coordination interface.

    Manages order creation, validation, and execution for backtests.
    """

    def create_order_from_signal(self, signal: Any) -> Any:
        """Create an order from a trading signal.

        Args:
            signal: StrategySignalEvent containing signal information

        Returns:
            OrderEvent object or None if no order should be created
        """
        ...

    def validate_and_execute_order(self, order: Any) -> Optional[Any]:
        """Validate and execute an order.

        Args:
            order: OrderEvent to validate and execute

        Returns:
            FillEvent if order was executed, None otherwise
        """
        ...

    def handle_fill_event(self, fill: Any) -> None:
        """Handle a fill event after order execution.

        Args:
            fill: FillEvent with execution details
        """
        ...
