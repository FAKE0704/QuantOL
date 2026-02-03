"""Service factory for backtest engine components.

This factory creates all services used by the backtest engine,
implementing dependency injection pattern.
"""

from typing import Optional, Dict, Any
from src.core.strategy.indicators import IndicatorService
from src.core.strategy.position_strategy import PositionStrategyFactory
from src.core.portfolio.portfolio import PortfolioManager
from src.core.risk.risk_manager import RiskManager
from src.core.execution.Trader import BacktestTrader, TradeOrderManager
from src.support.log.backtest_debug_logger import BacktestDebugLogger
from src.support.log.logger import logger

from ..services.database_provider import BacktestDatabaseProvider
from ..services.equity_service import EquityService
from ..services.results_service import ResultsService
from ..coordinators.event_coordinator import EventCoordinator
from ..coordinators.order_coordinator import OrderCoordinator


class BacktestServiceFactory:
    """Factory for creating backtest engine services.

    This factory encapsulates all service creation logic,
    making the BacktestEngine cleaner and more testable.
    """

    @staticmethod
    def create_database_provider(db_adapter) -> BacktestDatabaseProvider:
        """Create database provider.

        Args:
            db_adapter: Database adapter instance

        Returns:
            BacktestDatabaseProvider instance
        """
        return BacktestDatabaseProvider(db_adapter)

    @staticmethod
    def create_indicator_service() -> IndicatorService:
        """Create indicator service.

        Returns:
            IndicatorService instance
        """
        return IndicatorService()

    @staticmethod
    def create_position_strategy(config, debug_logger: BacktestDebugLogger):
        """Create position strategy based on config.

        Args:
            config: BacktestConfig instance
            debug_logger: Debug logger instance

        Returns:
            Position strategy instance
        """
        position_params = config.position_strategy_params
        min_lot_size = getattr(config, 'min_lot_size', 100)

        try:
            if config.position_strategy_type == "fixed_percent":
                from src.core.strategy.fixed_percent_position_strategy import FixedPercentPositionStrategy
                return FixedPercentPositionStrategy(
                    percent=position_params.get("percent", 0.1),
                    use_initial_capital=position_params.get("use_initial_capital", True),
                    min_lot_size=min_lot_size,
                    debug_logger=debug_logger
                )
            elif config.position_strategy_type == "martingale":
                from src.core.strategy.fixed_percent_position_strategy import MartingalePositionStrategy
                return MartingalePositionStrategy(
                    base_percent=position_params.get("base_percent", 5.0) / 100,
                    multiplier=position_params.get("multiplier", 2.0),
                    max_doubles=position_params.get("max_doubles", 5),
                    min_lot_size=min_lot_size,
                    debug_logger=debug_logger
                )
            else:
                # Fallback to old version
                return PositionStrategyFactory.create_strategy(
                    config.position_strategy_type,
                    config.initial_capital,
                    config.position_strategy_params
                )
        except Exception as e:
            logger.error(f"Position strategy creation failed: {e}, using default")
            from src.core.strategy.fixed_percent_position_strategy import FixedPercentPositionStrategy
            return FixedPercentPositionStrategy(
                percent=0.1,
                use_initial_capital=True,
                min_lot_size=min_lot_size,
                debug_logger=debug_logger
            )

    @staticmethod
    def create_portfolio_manager(config, position_strategy) -> PortfolioManager:
        """Create portfolio manager.

        Args:
            config: BacktestConfig instance
            position_strategy: Position strategy instance

        Returns:
            PortfolioManager instance
        """
        return PortfolioManager(
            initial_capital=config.initial_capital,
            position_strategy=position_strategy,
            event_bus=None  # No event bus in backtest mode
        )

    @staticmethod
    def create_risk_manager(portfolio, commission_rate: float) -> RiskManager:
        """Create risk manager.

        Args:
            portfolio: Portfolio instance
            commission_rate: Commission rate

        Returns:
            RiskManager instance
        """
        return RiskManager(portfolio, commission_rate)

    @staticmethod
    def create_trader(commission_rate: float) -> BacktestTrader:
        """Create backtest trader.

        Args:
            commission_rate: Commission rate

        Returns:
            BacktestTrader instance
        """
        return BacktestTrader(commission_rate=commission_rate)

    @staticmethod
    def create_trade_order_manager(db_provider, trader) -> TradeOrderManager:
        """Create trade order manager.

        Args:
            db_provider: Database provider
            trader: BacktestTrader instance

        Returns:
            TradeOrderManager instance

        Note:
            If db_provider has no adapter configured, will pass None to TradeOrderManager.
        """
        adapter = db_provider.get_adapter()
        return TradeOrderManager(adapter, trader)

    @staticmethod
    def create_equity_service(portfolio, initial_capital: float) -> EquityService:
        """Create equity service.

        Args:
            portfolio: Portfolio instance
            initial_capital: Initial capital amount

        Returns:
            EquityService instance
        """
        return EquityService(portfolio, initial_capital)

    @staticmethod
    def create_results_service(portfolio, equity_service) -> ResultsService:
        """Create results service.

        Args:
            portfolio: Portfolio instance
            equity_service: EquityService instance

        Returns:
            ResultsService instance
        """
        return ResultsService(portfolio, equity_service)

    @staticmethod
    def create_event_coordinator() -> EventCoordinator:
        """Create event coordinator.

        Returns:
            EventCoordinator instance
        """
        return EventCoordinator()

    @staticmethod
    def create_order_coordinator(
        portfolio,
        trader,
        trade_order_manager,
        position_strategy,
        config
    ) -> OrderCoordinator:
        """Create order coordinator.

        Args:
            portfolio: Portfolio instance
            trader: BacktestTrader instance
            trade_order_manager: TradeOrderManager instance
            position_strategy: Position strategy instance
            config: BacktestConfig instance

        Returns:
            OrderCoordinator instance
        """
        return OrderCoordinator(
            portfolio=portfolio,
            trader=trader,
            trade_order_manager=trade_order_manager,
            position_strategy=position_strategy,
            config=config
        )

    @staticmethod
    def create_ranking_service(config, indicator_service, data_dict, portfolio_manager):
        """Create cross-sectional ranking service if enabled.

        Args:
            config: BacktestConfig instance
            indicator_service: IndicatorService instance
            data_dict: Dictionary of symbol data
            portfolio_manager: PortfolioManager instance

        Returns:
            Tuple of (ranking_service, ranking_strategy) or (None, None)
        """
        if not config.enable_cross_sectional or not config.ranking_config:
            return None, None

        from src.core.strategy.cross_sectional.ranking_config import RankingConfig
        from src.core.strategy.cross_sectional.ranking_service import CrossSectionalRankingService
        from src.core.strategy.cross_sectional.ranking_strategy import RankingBasedStrategy

        ranking_config = RankingConfig(**config.ranking_config)
        ranking_service = CrossSectionalRankingService(
            indicator_service=indicator_service,
            ranking_config=ranking_config
        )
        ranking_strategy = RankingBasedStrategy(
            data_dict=data_dict,
            name="cross_sectional_ranking",
            ranking_service=ranking_service,
            portfolio_manager=portfolio_manager,
            indicator_service=indicator_service
        )

        logger.info(f"Cross-sectional ranking enabled: {ranking_config.factor_expression}")
        return ranking_service, ranking_strategy

    @staticmethod
    def create_rebalance_period_service(config):
        """Create rebalance period service if enabled.

        Args:
            config: BacktestConfig instance

        Returns:
            RebalancePeriodService instance or None
        """
        if not hasattr(config, 'rebalance_period_mode') or config.rebalance_period_mode == 'disabled':
            return None

        from src.services.rebalance_period_service import RebalancePeriodService

        rebalance_config = {
            "mode": config.rebalance_period_mode,
            **config.rebalance_period_params
        }
        service = RebalancePeriodService(rebalance_config)
        logger.info(f"Rebalance period service enabled: mode={config.rebalance_period_mode}")
        return service
