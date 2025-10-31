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
        print(f"[DEBUG] 开始初始化策略")
        print(f"[DEBUG] 是否多符号模式: {backtest_config.is_multi_symbol()}")

        if backtest_config.is_multi_symbol():
            print(f"[DEBUG] 多符号模式，初始化多符号策略...")
            self._initialize_multi_symbol_strategies(engine, backtest_config, data)
        else:
            print(f"[DEBUG] 单符号模式，初始化单符号策略...")
            self._initialize_single_symbol_strategies(engine, backtest_config, data)

    def _initialize_multi_symbol_strategies(self, engine: BacktestEngine, backtest_config: Any, data: Dict[str, Any]) -> None:
        """初始化多符号策略"""
        print(f"[DEBUG] 多符号策略初始化开始")
        print(f"[DEBUG] 符号列表: {list(data.keys())}")

        for symbol, symbol_data in data.items():
            print(f"[DEBUG] 处理符号: {symbol}")
            symbol_strategy_config = backtest_config.get_strategy_for_symbol(symbol)
            strategy_type = symbol_strategy_config.get('type', '使用默认策略')

            print(f"[DEBUG] 符号 {symbol} 策略类型: '{strategy_type}'")
            print(f"[DEBUG] 符号 {symbol} 策略配置: {symbol_strategy_config}")

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
        print(f"[DEBUG] 单符号策略初始化开始")
        print(f"[DEBUG] backtest_config 类型: {type(backtest_config)}")

        try:
            default_strategy = backtest_config.default_strategy
            print(f"[DEBUG] 获取到的 default_strategy: {default_strategy}")
            print(f"[DEBUG] default_strategy 类型: {type(default_strategy)}")
        except AttributeError as e:
            print(f"[DEBUG] 获取 default_strategy 失败: {e}")
            # 检查是否有其他属性
            for attr in ['strategy_type', 'default_strategy_type', 'strategy_mapping']:
                if hasattr(backtest_config, attr):
                    print(f"[DEBUG] 找到属性 {attr}: {getattr(backtest_config, attr)}")
            return

        if default_strategy is None:
            print(f"[DEBUG] default_strategy 为 None")
            return

        strategy_type = default_strategy.get('type', '使用默认策略')
        print(f"[DEBUG] 单符号策略类型: '{strategy_type}'")
        print(f"[DEBUG] 默认策略配置: {default_strategy}")
        print(f"[DEBUG] default_strategy 所有键: {list(default_strategy.keys()) if isinstance(default_strategy, dict) else 'N/A'}")

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
        elif strategy_type.startswith("规则组:") or strategy_type in ['Martingale', '金叉死叉', '相对强度']:
            print(f"[DEBUG] 单符号模式检测到规则组策略: {strategy_type}")
            strategy = self._create_rule_group_strategy(engine, 'default', data, strategy_type)
            if strategy:
                engine.register_strategy(strategy)
                print(f"[DEBUG] 单符号规则组策略注册成功: {strategy.name}")
            else:
                print(f"[DEBUG] 单符号规则组策略创建失败: {strategy_type}")
        else:
            print(f"[DEBUG] 单符号模式未知策略类型: {strategy_type}，跳过注册")

    def _create_rule_group_strategy(self, engine: BacktestEngine, symbol: str, symbol_data: Any, strategy_type: str):
        """创建规则组策略"""
        print(f"[DEBUG] 创建规则组策略: symbol={symbol}, strategy_type={strategy_type}")

        # 处理两种格式: "规则组: Martingale" 或直接 "Martingale"
        if strategy_type.startswith("规则组:"):
            group_name = strategy_type.replace("规则组: ", "")
        else:
            group_name = strategy_type

        print(f"[DEBUG] 解析规则组名称: {strategy_type} -> {group_name}")

        if 'rule_groups' in self.session_state:
            print(f"[DEBUG] 可用规则组: {list(self.session_state.rule_groups.keys())}")

            if group_name in self.session_state.rule_groups:
                group = self.session_state.rule_groups[group_name]
                print(f"[DEBUG] 规则组内容: {group}")

                strategy = RuleBasedStrategy(
                    Data=symbol_data,
                    name=f"规则组策略_{symbol}_{group_name}",
                    indicator_service=self.session_state.indicator_service,
                    buy_rule_expr=group.get('buy_rule', ''),
                    sell_rule_expr=group.get('sell_rule', ''),
                    open_rule_expr=group.get('open_rule', ''),
                    close_rule_expr=group.get('close_rule', ''),
                    portfolio_manager=engine.portfolio_manager
                )

                print(f"[DEBUG] 规则组策略创建成功: {strategy.name}")
                print(f"[DEBUG] 开仓规则: {strategy.open_rule_expr}")
                print(f"[DEBUG] 清仓规则: {strategy.close_rule_expr}")
                print(f"[DEBUG] 加仓规则: {strategy.buy_rule_expr}")
                print(f"[DEBUG] 平仓规则: {strategy.sell_rule_expr}")

                return strategy
            else:
                print(f"[DEBUG] 规则组 '{group_name}' 不存在")
        else:
            print(f"[DEBUG] session_state 中没有 rule_groups")

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

    async def load_data_for_backtest(self, backtest_config: Any, start_date: str, end_date: str) -> Any:
        """加载回测所需数据"""
        print(f"[DEBUG] 开始加载回测数据")
        symbols = backtest_config.get_symbols()
        print(f"[DEBUG] 目标符号: {symbols}")
        print(f"[DEBUG] 时间范围: {start_date} 至 {end_date}")
        print(f"[DEBUG] 数据频率: {backtest_config.frequency}")

        if backtest_config.is_multi_symbol():
            # 多符号模式
            print(f"[DEBUG] 多符号模式，加载数据...")
            data = await self.session_state.db.load_multiple_stock_data(
                symbols, start_date, end_date, backtest_config.frequency
            )
            print(f"[DEBUG] 多符号数据加载完成: {len(data)} 只股票")
        else:
            # 单符号模式
            print(f"[DEBUG] 单符号模式，加载数据...")
            data = await self.session_state.db.load_stock_data(
                symbols[0], start_date, end_date, backtest_config.frequency
            )
            if data is not None:
                print(f"[DEBUG] 单符号数据加载完成: {len(data)} 条记录")
            else:
                print(f"[DEBUG] 单符号数据加载失败")

        return data

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