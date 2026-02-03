"""Refactored backtest engine.

This is the refactored version of BacktestEngine with separated concerns,
following dependency injection and single responsibility principles.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta, date
from typing import Optional, Dict, Any, List, Type
import pandas as pd
import numpy as np
import asyncio
import logging

from src.core.strategy.indicators import IndicatorService
from src.core.strategy.rule_parser import RuleParser
from src.core.strategy.rule_based_strategy import RuleBasedStrategy
from src.core.strategy.signal_types import SignalType
from src.event_bus.event_types import (
    StrategyScheduleEvent, TradingDayEvent, StrategySignalEvent,
    OrderEvent, FillEvent
)
from src.support.log.logger import logger
from src.support.log.backtest_debug_logger import BacktestDebugLogger

# Import refactored components
from .factories import BacktestServiceFactory
from .services.database_provider import BacktestDatabaseProvider
from .services.equity_service import EquityService
from .services.results_service import ResultsService
from .coordinators.event_coordinator import EventCoordinator
from .coordinators.order_coordinator import OrderCoordinator

# Import original config (keeping for compatibility)
from src.core.strategy.backtesting import BacktestConfig

logger.setLevel(logging.DEBUG)


@dataclass
class BacktestConfig:
    """回测配置类 - 保持与原始配置的兼容性"""
    start_date: str
    end_date: str
    target_symbol: str
    frequency: str
    target_symbols: List[str] = field(default_factory=list)

    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    max_holding_days: Optional[int] = None
    extra_params: Optional[Dict[str, Any]] = None
    initial_capital: float = 1e6
    commission_rate: float = 0.0005
    slippage: float = 0.00
    strategy_type: str = "月定投"
    position_strategy_type: str = "fixed_percent"
    position_strategy_params: Dict[str, Any] = field(default_factory=dict)
    min_lot_size: int = 100

    rebalance_period_mode: str = "disabled"
    rebalance_period_params: Dict[str, Any] = field(default_factory=dict)

    strategy_mapping: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    default_strategy: Dict[str, Any] = field(default_factory=dict)

    default_strategy_type: str = "月定投"
    custom_rules: Optional[Dict[str, str]] = None
    default_custom_rules: Optional[Dict[str, str]] = None
    strategy_inheritance: Optional[Dict[str, Any]] = None

    enable_cross_sectional: bool = False
    ranking_config: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        """参数验证和兼容性处理"""
        self.commission_rate = self.commission_rate
        self.slippage = float(self.slippage)
        self.start_date = self._normalize_date_format(self.start_date)
        self.end_date = self._normalize_date_format(self.end_date)

    @staticmethod
    def _normalize_date_format(date_str: str) -> str:
        """标准化日期格式为 %Y%m%d"""
        if not date_str:
            return date_str
        for fmt in ('%Y-%m-%d', '%Y/%m/%d', '%Y%m%d'):
            try:
                return datetime.strptime(date_str, fmt).strftime('%Y%m%d')
            except ValueError:
                continue
        return date_str

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "start_date": self.start_date,
            "end_date": self.end_date,
            "target_symbol": self.target_symbol,
            "frequency": self.frequency,
            "target_symbols": self.target_symbols.copy(),
            "initial_capital": self.initial_capital,
            "commission_rate": self.commission_rate,
            "slippage": self.slippage,
            "strategy_type": self.strategy_type,
            "position_strategy_type": self.position_strategy_type,
            "position_strategy_params": self.position_strategy_params.copy(),
            "min_lot_size": self.min_lot_size,
            "rebalance_period_mode": self.rebalance_period_mode,
            "rebalance_period_params": self.rebalance_period_params.copy(),
            "enable_cross_sectional": self.enable_cross_sectional,
            "ranking_config": self.ranking_config.copy() if self.ranking_config else None,
        }

    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> "BacktestConfig":
        """从字典创建配置实例"""
        return cls(**config_dict)


class BacktestEngine:
    """Refactored backtest engine - orchestrates services using dependency injection.

    This version delegates specialized responsibilities to:
    - EquityService: Equity tracking and calculation
    - ResultsService: Results aggregation and metrics
    - EventCoordinator: Event queue management
    - OrderCoordinator: Order creation and execution
    - BacktestDatabaseProvider: Database access
    """

    def __init__(
        self,
        config: BacktestConfig,
        data,
        progress_callback=None,
        db_adapter=None,
        backtest_id: str = None
    ):
        """Initialize backtest engine using dependency injection.

        Args:
            config: BacktestConfig instance
            data: DataFrame or dict of DataFrames with price data
            progress_callback: Optional progress callback function
            db_adapter: Optional database adapter
            backtest_id: Optional backtest ID
        """
        self.config = config
        self.current_price = None
        self.current_time = None
        self.current_index = None
        self.progress_callback = progress_callback
        self._last_progress_update = 0
        self.trades = []
        self.results = {}
        self.errors = []
        self.strategies = []

        # Backtest ID and debug logger
        self.backtest_id = backtest_id or f"bt_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        strategy_name = config.strategy_type or "未命名策略"
        self.debug_logger = BacktestDebugLogger(
            backtest_id=self.backtest_id,
            strategy_name=strategy_name,
            config=config.to_dict()
        )

        # Support single and multi-symbol modes
        if isinstance(data, dict):
            self.multi_symbol_mode = True
            self.data_dict = data
            first_symbol = next(iter(data.keys()))
            self.data = data[first_symbol]
        else:
            self.multi_symbol_mode = False
            self.data_dict = {config.target_symbol: data}
            self.data = data

        # Use factory to create services (dependency injection)
        self.db_provider = BacktestServiceFactory.create_database_provider(db_adapter)
        self.indicator_service = BacktestServiceFactory.create_indicator_service()
        self.position_strategy = BacktestServiceFactory.create_position_strategy(
            config, self.debug_logger
        )
        self.portfolio_manager = BacktestServiceFactory.create_portfolio_manager(
            config, self.position_strategy
        )
        self.risk_manager = BacktestServiceFactory.create_risk_manager(
            self.portfolio_manager, config.commission_rate
        )

        # Create advanced services
        self.equity_service = BacktestServiceFactory.create_equity_service(
            self.portfolio_manager, config.initial_capital
        )
        self.results_service = BacktestServiceFactory.create_results_service(
            self.portfolio_manager, self.equity_service
        )
        self.event_coordinator = BacktestServiceFactory.create_event_coordinator()

        # Create trader and order manager
        self.backtest_trader = BacktestServiceFactory.create_trader(
            config.commission_rate
        )
        self.trade_order_manager = BacktestServiceFactory.create_trade_order_manager(
            self.db_provider, self.backtest_trader
        )

        # Create order coordinator
        self.order_coordinator = BacktestServiceFactory.create_order_coordinator(
            self.portfolio_manager,
            self.backtest_trader,
            self.trade_order_manager,
            self.position_strategy,
            config
        )

        # Create rule parser
        self.rule_parser = RuleParser(self.data, self.indicator_service)
        self.rule_parser.portfolio_manager = self.portfolio_manager

        # Register event handlers
        self.event_coordinator.register_handler(
            StrategySignalEvent, self._handle_signal_event
        )
        self.event_coordinator.register_handler(
            OrderEvent, self._handle_order_event
        )
        self.event_coordinator.register_handler(
            FillEvent, self._handle_fill_event
        )

        # Initialize cross-sectional ranking if enabled
        self.ranking_service = None
        self.ranking_strategy = None
        if config.enable_cross_sectional and config.ranking_config:
            if not self.multi_symbol_mode:
                raise ValueError("Cross-sectional ranking requires multi-symbol mode")
            self.ranking_service, self.ranking_strategy = (
                BacktestServiceFactory.create_ranking_service(
                    config,
                    self.indicator_service,
                    self.data_dict,
                    self.portfolio_manager
                )
            )
            if self.ranking_strategy:
                self.register_strategy(self.ranking_strategy)

        # Initialize rebalance period service
        self.rebalance_period_service = (
            BacktestServiceFactory.create_rebalance_period_service(config)
        )

        # Portfolio interface
        self.portfolio = self.portfolio_manager

    @property
    def db(self):
        """Get database adapter through provider."""
        return self.db_provider.db

    def register_handler(self, event_type: Type, handler):
        """Register event handler through coordinator.

        Args:
            event_type: Event class to handle
            handler: Handler function
        """
        self.event_coordinator.register_handler(event_type, handler)

    def push_event(self, event):
        """Push event to queue through coordinator.

        Args:
            event: Event object to queue
        """
        self.event_coordinator.push_event(event)

    def register_strategy(self, strategy):
        """Register a strategy instance.

        Args:
            strategy: Strategy instance with handle_event method and strategy_id attribute
        """
        if not hasattr(strategy, 'handle_event'):
            raise ValueError("Strategy must implement handle_event method")
        if not hasattr(strategy, 'strategy_id'):
            raise ValueError("Strategy must have strategy_id attribute")

        if not strategy.strategy_id or not isinstance(strategy.strategy_id, str):
            raise ValueError(f"Invalid strategy ID: {strategy.strategy_id}")

        existing_ids = [s.strategy_id for s in self.strategies]
        if strategy.strategy_id in existing_ids:
            raise ValueError(f"Strategy ID {strategy.strategy_id} already exists")

        self.strategies.append(strategy)

        strategy_name = getattr(strategy, 'name', 'unnamed')
        logger.debug(
            f"Strategy registered: ID={strategy.strategy_id}, "
            f"Name={strategy_name}, Type={type(strategy).__name__}"
        )

        self.register_handler(StrategyScheduleEvent, strategy.on_schedule)
        logger.debug(f"Registered schedule handler for {strategy.strategy_id}")
        logger.info(f"Strategy registered: ID={strategy.strategy_id}, Name={strategy_name}")

    def update_rule_parser_data(self):
        """Update RuleParser data references."""
        self.rule_parser.data = self.data
        self.rule_parser.indicator_service = self.indicator_service
        self.rule_parser.portfolio_manager = self.portfolio_manager

    async def run(self, start_date: datetime, end_date: datetime):
        """Execute event-driven backtest (async version).

        Args:
            start_date: Backtest start date
            end_date: Backtest end date
        """
        # Auto cleanup old logs
        try:
            from src.utils.log_cleaner import auto_cleanup_on_backtest_start
            auto_cleanup_on_backtest_start()
        except Exception as e:
            logger.warning(f"Auto cleanup failed: {e}")

        # Update RuleParser data references
        self.update_rule_parser_data()

        # Filter data by date range
        start_str = start_date.strftime('%Y%m%d')
        end_str = end_date.strftime('%Y%m%d')

        # Convert timestamps to comparable format
        if hasattr(self.data.index, 'to_pydatetime'):
            data_dates = pd.to_datetime(self.data.index).strftime('%Y%m%d')
        else:
            data_dates = self.data.index

        mask = (data_dates >= start_str) & (data_dates <= end_str)
        filtered_data = self.data[mask]

        logger.info(
            f"Starting backtest: {len(filtered_data)} data points from "
            f"{start_date} to {end_date}"
        )

        # Main backtest loop
        for idx, row in filtered_data.iterrows():
            try:
                self.current_index = idx
                self.current_time = idx

                # Get current price
                if hasattr(row, 'close'):
                    price = row['close']
                elif 'close' in row:
                    price = row['close']
                else:
                    continue

                self.current_price = price

                # Update equity through service
                self.equity_service.update_equity(idx, price)

                # Generate TradingDayEvent
                trading_day_event = TradingDayEvent(timestamp=idx, price=price)
                self.push_event(trading_day_event)

                # Execute strategies
                for strategy in self.strategies:
                    if hasattr(strategy, 'on_data'):
                        await strategy.on_data(row, idx)
                    elif hasattr(strategy, 'handle_event'):
                        await strategy.handle_event(trading_day_event)

                # Process event queue
                self.event_coordinator.process_event_queue()

                # Update progress
                if self.progress_callback:
                    current_idx = list(filtered_data.index).index(idx)
                    total = len(filtered_data)
                    if current_idx - self._last_progress_update >= max(1, total // 100):
                        progress = current_idx / total
                        await self.progress_callback(progress, idx)
                        self._last_progress_update = current_idx

                # Yield control to event loop
                await asyncio.sleep(0)

            except Exception as e:
                logger.error(f"Error in backtest loop at {idx}: {e}", exc_info=True)
                continue

        # Sync debug_data after loop completes
        logger.info("Backtest loop complete, syncing debug_data...")
        for strategy in self.strategies:
            if hasattr(strategy, 'parser') and hasattr(strategy, 'debug_data'):
                if id(strategy.parser.data) != id(strategy.debug_data):
                    old_cols = len(strategy.debug_data.columns)
                    strategy.debug_data = strategy.parser.data.copy()
                    new_cols = len(strategy.debug_data.columns)
                    logger.info(
                        f"Strategy {strategy.name}: debug_data synced, "
                        f"columns from {old_cols} to {new_cols}"
                    )

    def _handle_signal_event(self, event: StrategySignalEvent):
        """Handle strategy signal event.

        Args:
            event: StrategySignalEvent
        """
        idx = getattr(event, 'current_index', self.current_index)
        logger.info(
            f"Handling signal: type={event.signal_type}, symbol={event.symbol}, "
            f"price={event.price}, index={idx}"
        )

        rule_name = getattr(event, 'rule_name', '')
        self.debug_logger.log_signal(
            index=idx,
            signal_type=str(event.signal_type),
            symbol=event.symbol,
            price=float(event.price),
            rule_name=rule_name
        )

        # Record signal in data
        if event.signal_type in [SignalType.OPEN, SignalType.BUY]:
            self.data.loc[idx, 'signal'] = 1
        elif event.signal_type in [SignalType.SELL, SignalType.CLOSE, SignalType.LIQUIDATE]:
            self.data.loc[idx, 'signal'] = -1
        elif event.signal_type == SignalType.HEDGE:
            self.data.loc[idx, 'signal'] = 2
        elif event.signal_type == SignalType.REBALANCE:
            self.data.loc[idx, 'signal'] = 3

        # Create order using order coordinator
        order = self.order_coordinator.create_order_from_signal(event)
        if order:
            self.push_event(order)

    def _handle_order_event(self, event: OrderEvent):
        """Handle order event.

        Args:
            event: OrderEvent
        """
        logger.debug(f"Handling order event: {event}")

        # Calculate order amount and commission
        order_amount = float(event.quantity) * float(event.price)
        commission = order_amount * self.config.commission_rate
        total_cost = order_amount + commission

        # Determine quantity direction
        quantity = event.quantity if event.direction == 'BUY' else -event.quantity

        # Update portfolio
        success = self.portfolio_manager.update_position(
            symbol=event.symbol,
            quantity=quantity,
            price=event.price,
            commission=commission
        )

        if not success:
            self.log_error(f"Order execution failed: {event.direction} {event.quantity}@{event.price}")
            return

        # Record trade
        trade_record = {
            'timestamp': self.current_time,
            'symbol': event.symbol,
            'direction': event.direction,
            'price': event.price,
            'quantity': event.quantity,
            'commission': commission,
            'total_cost': total_cost if event.direction == 'BUY' else -total_cost
        }

        # Add martingale_level if applicable
        if hasattr(self.position_strategy, 'get_martingale_level'):
            trade_record['martingale_level'] = self.position_strategy.get_martingale_level(
                event.symbol
            )

        self.trades.append(trade_record)

        self.debug_logger.log_trade_executed(
            index=self.current_index if self.current_index is not None else 0,
            direction=event.direction,
            symbol=event.symbol,
            quantity=event.quantity,
            price=float(event.price),
            commission=commission
        )

    def _handle_fill_event(self, event: FillEvent):
        """Handle fill event.

        Args:
            event: FillEvent
        """
        logger.debug(f"Handling fill event: {event}")
        # Fill events are already processed in order handler
        # This method exists for compatibility with event system

    def log_error(self, message: str):
        """Log error message.

        Args:
            message: Error message
        """
        error_entry = {
            'timestamp': datetime.now().isoformat(),
            'message': message,
            'current_capital': self.portfolio_manager.get_available_cash(),
            'position': self.portfolio_manager.get_all_positions()
        }
        self.errors.append(error_entry)
        logger.error(f"ERROR | {message}")

    def get_results(self) -> Dict[str, Any]:
        """Get backtest results through results service.

        Returns:
            Dictionary with backtest results and metrics
        """
        # Collect debug data
        debug_data = {}
        parser_data = {}

        for strategy in self.strategies:
            strategy_name = getattr(strategy, 'name', 'unknown')
            if hasattr(strategy, 'debug_data') and strategy.debug_data is not None:
                debug_data[strategy_name] = strategy.debug_data
            if hasattr(strategy, 'parser') and strategy.parser.data is not None:
                parser_data[strategy_name] = strategy.parser.data

        # Prepare price data
        price_data = self.data.copy() if hasattr(self, 'data') and not self.data.empty else None

        # Prepare signals data
        signals_data = None
        if price_data is not None and 'signal' in price_data.columns:
            signals_data = price_data[price_data['signal'] != 0][['signal']].copy()

        # Use results service to aggregate
        results = self.results_service.get_results(
            trades=self.trades,
            debug_data=debug_data,
            parser_data=parser_data,
            price_data=price_data,
            signals_data=signals_data
        )

        results['errors'] = self.errors
        return results

    def create_rule_based_strategy(
        self,
        name: str,
        buy_rule_expr: str = "",
        sell_rule_expr: str = ""
    ) -> RuleBasedStrategy:
        """Create a rule-based strategy instance.

        Args:
            name: Strategy name
            buy_rule_expr: Buy rule expression
            sell_rule_expr: Sell rule expression

        Returns:
            RuleBasedStrategy instance
        """
        return RuleBasedStrategy(
            Data=self.data,
            name=name,
            indicator_service=self.indicator_service,
            buy_rule_expr=buy_rule_expr,
            sell_rule_expr=sell_rule_expr
        )
