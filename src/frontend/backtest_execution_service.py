import streamlit as st
import pandas as pd
from typing import Dict, Any, List
from src.core.strategy.backtesting import BacktestEngine
from src.core.strategy.rule_based_strategy import RuleBasedStrategy
from src.core.strategy.strategy import FixedInvestmentStrategy
from src.event_bus.event_types import StrategySignalEvent
from src.core.strategy.event_handlers import handle_signal
from src.core.strategy.signal_types import SignalType

class BacktestExecutionService:
    """回测执行服务，负责回测引擎的初始化和执行"""

    def __init__(self, session_state):
        self.session_state = session_state

    def initialize_engine(self, backtest_config: Any, data: Any) -> BacktestEngine:
        """初始化回测引擎"""
        engine = BacktestEngine(config=backtest_config, data=data)

        # 注册信号处理器
        engine.register_handler(StrategySignalEvent, self._create_signal_handler(engine))

        # 初始化指标服务
        self._initialize_indicator_service()

        # 初始化策略
        self._initialize_strategies(engine, backtest_config, data)

        return engine

    def _create_signal_handler(self, engine: BacktestEngine):
        """创建信号事件处理器"""
        def handle_signal_with_direction(event: StrategySignalEvent):
            # 保持向后兼容性
            if not hasattr(event, 'signal_type') or event.signal_type is None:
                event.signal_type = SignalType.BUY if event.confidence > 0 else SignalType.SELL
            return handle_signal(event)

        return handle_signal_with_direction

    def _initialize_indicator_service(self) -> None:
        """初始化指标服务"""
        if 'indicator_service' not in self.session_state:
            from src.core.strategy.indicators import IndicatorService
            self.session_state.indicator_service = IndicatorService()

    def _initialize_strategies(self, engine: BacktestEngine, backtest_config: Any, data: Any) -> None:
        """初始化策略实例"""
        if backtest_config.is_multi_symbol():
            self._initialize_multi_symbol_strategies(engine, backtest_config, data)
        else:
            self._initialize_single_symbol_strategies(engine, backtest_config, data)

    def _initialize_multi_symbol_strategies(self, engine: BacktestEngine, backtest_config: Any, data: Dict[str, Any]) -> None:
        """初始化多符号策略"""
        for symbol, symbol_data in data.items():
            symbol_strategy_config = backtest_config.get_strategy_for_symbol(symbol)
            strategy_type = symbol_strategy_config.get('type', '使用默认策略')

            if strategy_type == "月定投":
                strategy = FixedInvestmentStrategy(
                    Data=symbol_data,
                    name=f"月定投策略_{symbol}",
                    buy_rule_expr="True",
                    sell_rule_expr="False"
                )
            elif strategy_type == "自定义规则":
                strategy = RuleBasedStrategy(
                    Data=symbol_data,
                    name=f"自定义规则策略_{symbol}",
                    indicator_service=self.session_state.indicator_service,
                    buy_rule_expr=symbol_strategy_config.get('buy_rule', ''),
                    sell_rule_expr=symbol_strategy_config.get('sell_rule', ''),
                    open_rule_expr=symbol_strategy_config.get('open_rule', ''),
                    close_rule_expr=symbol_strategy_config.get('close_rule', ''),
                    portfolio_manager=engine.portfolio_manager
                )
            elif strategy_type.startswith("规则组:"):
                strategy = self._create_rule_group_strategy(engine, symbol, symbol_data, strategy_type)
            else:
                continue

            engine.register_strategy(strategy)

    def _initialize_single_symbol_strategies(self, engine: BacktestEngine, backtest_config: Any, data: Any) -> None:
        """初始化单符号策略"""
        default_strategy = backtest_config.default_strategy
        strategy_type = default_strategy.get('type', '使用默认策略')

        if strategy_type == "月定投":
            strategy = FixedInvestmentStrategy(
                Data=data,
                name="月定投策略",
                buy_rule_expr="True",
                sell_rule_expr="False"
            )
        elif strategy_type == "自定义规则":
            strategy = RuleBasedStrategy(
                Data=data,
                name="自定义规则策略",
                indicator_service=self.session_state.indicator_service,
                buy_rule_expr=default_strategy.get('buy_rule', ''),
                sell_rule_expr=default_strategy.get('sell_rule', ''),
                open_rule_expr=default_strategy.get('open_rule', ''),
                close_rule_expr=default_strategy.get('close_rule', ''),
                portfolio_manager=engine.portfolio_manager
            )
        else:
            return

        engine.register_strategy(strategy)

    def _create_rule_group_strategy(self, engine: BacktestEngine, symbol: str, symbol_data: Any, strategy_type: str):
        """创建规则组策略"""
        group_name = strategy_type.replace("规则组: ", "")
        if 'rule_groups' in self.session_state and group_name in self.session_state.rule_groups:
            group = self.session_state.rule_groups[group_name]
            return RuleBasedStrategy(
                Data=symbol_data,
                name=f"规则组策略_{symbol}_{group_name}",
                indicator_service=self.session_state.indicator_service,
                buy_rule_expr=group.get('buy_rule', ''),
                sell_rule_expr=group.get('sell_rule', ''),
                open_rule_expr=group.get('open_rule', ''),
                close_rule_expr=group.get('close_rule', ''),
                portfolio_manager=engine.portfolio_manager
            )
        return None

    def execute_backtest(self, engine: BacktestEngine, backtest_config: Any) -> Dict[str, Any]:
        """执行回测"""
        # 启动事件循环
        task_id = f"backtest_{self.session_state.strategy_id}"

        # 执行回测
        if backtest_config.is_multi_symbol():
            engine.run_multi_symbol(pd.to_datetime(backtest_config.start_date), pd.to_datetime(backtest_config.end_date))
        else:
            engine.run(pd.to_datetime(backtest_config.start_date), pd.to_datetime(backtest_config.end_date))

        # 获取结果
        results = engine.get_results()
        return results

    def prepare_chart_service(self, data: Any, equity_data: Any) -> None:
        """准备图表服务"""
        from src.services.chart_service import ChartService, DataBundle

        @st.cache_resource(ttl=3600, show_spinner=False)
        def init_chart_service(raw_data, transaction_data):
            if isinstance(raw_data, dict):
                # 多符号模式：使用第一个符号的数据作为主数据
                first_symbol = next(iter(raw_data.keys()))
                raw_data = raw_data[first_symbol]

            raw_data['open'] = raw_data['open'].astype(float)
            raw_data['high'] = raw_data['high'].astype(float)
            raw_data['low'] = raw_data['low'].astype(float)
            raw_data['close'] = raw_data['close'].astype(float)
            raw_data['combined_time'] = pd.to_datetime(raw_data['combined_time'])
            # 作图前时间排序
            raw_data = raw_data.sort_values(by='combined_time')
            transaction_data = transaction_data.sort_values(by='timestamp')
            databundle = DataBundle(raw_data, transaction_data, capital_flow_data=None)
            return ChartService(databundle)

        if 'chart_service' not in self.session_state:
            self.session_state.chart_service = init_chart_service(data, equity_data)
            self.session_state.chart_instance_id = id(self.session_state.chart_service)