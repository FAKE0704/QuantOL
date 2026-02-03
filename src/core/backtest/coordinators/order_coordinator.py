"""Order coordinator for backtest engine.

This coordinator manages order creation, validation, and execution,
extracted from BacktestEngine's order handling methods.
"""

from typing import Optional, Dict, Any
from datetime import datetime
from src.event_bus.event_types import StrategySignalEvent, OrderEvent, FillEvent
from src.support.log.logger import logger


class OrderCoordinator:
    """Order execution coordination service for backtest engine.

    Manages order creation from signals, validation, and execution.
    Extracted from BacktestEngine._handle_signal_event and related methods.
    """

    def __init__(
        self,
        portfolio,
        trader,
        trade_order_manager,
        position_strategy,
        config
    ):
        """Initialize order coordinator.

        Args:
            portfolio: Portfolio manager instance
            trader: BacktestTrader instance
            trade_order_manager: TradeOrderManager instance
            position_strategy: Position strategy instance
            config: BacktestConfig instance
        """
        self.portfolio = portfolio
        self.trader = trader
        self.trade_order_manager = trade_order_manager
        self.position_strategy = position_strategy
        self.config = config
        self._logger = logger.getChild('OrderCoordinator')

    def create_order_from_signal(self, signal: StrategySignalEvent) -> Optional[OrderEvent]:
        """Create an order from a trading signal.

        Args:
            signal: StrategySignalEvent containing signal information

        Returns:
            OrderEvent object or None if no order should be created
        """
        try:
            symbol = signal.symbol
            signal_type = signal.signal_type.value
            timestamp = signal.timestamp

            # Get current price from signal
            price = signal.price if hasattr(signal, 'price') else None
            if price is None:
                self._logger.warning(f"Signal missing price for {symbol}")
                return None

            # Determine order quantity based on position strategy
            quantity = self._calculate_order_quantity(
                symbol, signal_type, price, signal
            )

            if quantity == 0:
                self._logger.debug(f"Zero quantity calculated for {symbol}, skipping order")
                return None

            # Create order event
            order = OrderEvent(
                symbol=symbol,
                order_type='market',
                quantity=quantity,
                direction=signal_type,  # 'buy' or 'sell'
                price=price,
                timestamp=timestamp
            )

            self._logger.info(
                f"Created order: {signal_type} {quantity} {symbol} @ {price}"
            )
            return order

        except Exception as e:
            self._logger.error(f"Failed to create order from signal: {e}")
            return None

    def _calculate_order_quantity(
        self,
        symbol: str,
        signal_type: str,
        price: float,
        signal: StrategySignalEvent
    ) -> int:
        """Calculate order quantity based on position strategy.

        Args:
            symbol: Trading symbol
            signal_type: Signal type ('buy' or 'sell')
            price: Current price
            signal: Original signal event

        Returns:
            Order quantity (positive for buy, negative for sell)
        """
        # Check if signal has explicit quantity
        if hasattr(signal, 'quantity') and signal.quantity is not None:
            return signal.quantity

        # Use position strategy to calculate quantity
        available_cash = self.portfolio.get_available_cash()
        current_position = self.portfolio.get_position(symbol)

        if signal_type == 'buy':
            # Calculate buy quantity based on available cash
            quantity = self.position_strategy.calculate_buy_quantity(
                symbol=symbol,
                price=price,
                available_cash=available_cash,
                current_position=current_position
            )
        elif signal_type == 'sell':
            # Calculate sell quantity based on current position
            quantity = self.position_strategy.calculate_sell_quantity(
                symbol=symbol,
                price=price,
                current_position=current_position
            )
            # Make sell quantity negative
            quantity = -abs(quantity)
        else:
            self._logger.warning(f"Unknown signal type: {signal_type}")
            return 0

        # Apply min lot size rounding
        min_lot = getattr(self.config, 'min_lot_size', 100)
        if signal_type == 'buy':
            quantity = (quantity // min_lot) * min_lot

        return int(quantity)

    def validate_and_execute_order(self, order: OrderEvent) -> Optional[FillEvent]:
        """Validate and execute an order.

        Args:
            order: OrderEvent to validate and execute

        Returns:
            FillEvent if order was executed, None otherwise
        """
        try:
            # Validate order
            if not self._validate_order(order):
                self._logger.warning(f"Order validation failed: {order.symbol}")
                return None

            # Execute order through trader
            fill = self.trader.execute_order(order)

            if fill:
                self._logger.info(
                    f"Order executed: {fill.direction} {fill.filled_quantity} "
                    f"{fill.symbol} @ {fill.fill_price}"
                )
                return fill
            else:
                self._logger.warning(f"Order execution returned None: {order.symbol}")
                return None

        except Exception as e:
            self._logger.error(f"Failed to execute order: {e}")
            return None

    def _validate_order(self, order: OrderEvent) -> bool:
        """Validate order before execution.

        Args:
            order: OrderEvent to validate

        Returns:
            True if order is valid, False otherwise
        """
        # Check quantity
        if order.quantity == 0:
            self._logger.debug("Order quantity is zero")
            return False

        # Check price
        if order.price <= 0:
            self._logger.warning(f"Invalid price: {order.price}")
            return False

        # Check if we have enough cash for buy orders
        if order.direction == 'buy':
            required_cash = order.quantity * order.price
            available_cash = self.portfolio.get_available_cash()
            if required_cash > available_cash:
                self._logger.debug(
                    f"Insufficient cash: need {required_cash}, have {available_cash}"
                )
                return False

        # Check if we have enough position for sell orders
        elif order.direction == 'sell':
            current_position = self.portfolio.get_position(order.symbol)
            if abs(order.quantity) > current_position.quantity:
                self._logger.debug(
                    f"Insufficient position: selling {abs(order.quantity)}, "
                    f"have {current_position.quantity}"
                )
                return False

        return True

    def handle_fill_event(self, fill: FillEvent) -> None:
        """Handle a fill event after order execution.

        Args:
            fill: FillEvent with execution details
        """
        try:
            # Update portfolio
            if fill.direction == 'buy':
                self.portfolio.update_position(
                    symbol=fill.symbol,
                    quantity=fill.filled_quantity,
                    price=fill.fill_price,
                    timestamp=fill.timestamp
                )
            elif fill.direction == 'sell':
                self.portfolio.update_position(
                    symbol=fill.symbol,
                    quantity=-fill.filled_quantity,
                    price=fill.fill_price,
                    timestamp=fill.timestamp
                )

            self._logger.info(
                f"Fill processed: portfolio updated for {fill.symbol}"
            )

        except Exception as e:
            self._logger.error(f"Failed to handle fill event: {e}")
