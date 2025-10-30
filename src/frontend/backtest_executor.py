import streamlit as st
import pandas as pd
import numpy as np
from src.core.strategy.backtesting import BacktestEngine
from src.core.strategy.rule_based_strategy import RuleBasedStrategy
from src.core.strategy.strategy import FixedInvestmentStrategy
from src.core.strategy.signal_types import SignalType
from src.services.progress_service import progress_service
from typing import Dict, Any, List
import asyncio
from src.support.log.logger import logger

class BacktestExecutor:
    """回测执行器，负责回测引擎的初始化和执行"""

    def __init__(self, session_state):
        self.session_state = session_state

    async def load_data_for_backtest(self, backtest_config, start_date, end_date):
        """加载回测所需数据"""
        symbols = backtest_config.get_symbols()

        if backtest_config.is_multi_symbol():
            # 多符号模式
            data = await self.session_state.db.load_multiple_stock_data(
                symbols, start_date, end_date, backtest_config.frequency
            )
            st.info(f"已加载 {len(data)} 只股票数据")
        else:
            # 单符号模式
            data = await self.session_state.db.load_stock_data(
                symbols[0], start_date, end_date, backtest_config.frequency
            )

        return data

    def initialize_backtest_engine(self, backtest_config, data):
        """初始化回测引擎"""
        engine = BacktestEngine(config=backtest_config, data=data)

        # 注册事件处理器
        def handle_signal_with_direction(event):
            if not hasattr(event, 'signal_type') or event.signal_type is None:
                event.signal_type = SignalType.BUY if event.confidence > 0 else SignalType.SELL
            from src.core.strategy.event_handlers import handle_signal
            return handle_signal(event)

        engine.register_handler(type(event), handle_signal_with_direction)

        return engine

    def initialize_indicator_service(self):
        """初始化指标服务"""
        if 'indicator_service' not in self.session_state:
            from src.core.strategy.indicators import IndicatorService
            self.session_state.indicator_service = IndicatorService()

    def register_strategies(self, engine, backtest_config, data):
        """注册策略到回测引擎"""
        if backtest_config.is_multi_symbol():
            # 多符号模式：为每个符号创建独立的策略实例
            for symbol, symbol_data in data.items():
                self._register_symbol_strategy(engine, symbol, symbol_data, backtest_config)
        else:
            # 单符号模式（保持向后兼容）
            self._register_single_symbol_strategy(engine, data, backtest_config)

    def _register_symbol_strategy(self, engine, symbol, symbol_data, backtest_config):
        """为单个符号注册策略"""
        symbol_strategy_config = backtest_config.get_strategy_for_symbol(symbol)
        strategy_type = symbol_strategy_config.get('type', '使用默认策略')

        if strategy_type == "月定投":
            fixed_strategy = FixedInvestmentStrategy(
                Data=symbol_data,
                name=f"月定投策略_{symbol}",
                buy_rule_expr="True",
                sell_rule_expr="False"
            )
            engine.register_strategy(fixed_strategy)
        elif strategy_type == "自定义规则":
            rule_strategy = RuleBasedStrategy(
                Data=symbol_data,
                name=f"自定义规则策略_{symbol}",
                indicator_service=self.session_state.indicator_service,
                buy_rule_expr=symbol_strategy_config.get('buy_rule', ''),
                sell_rule_expr=symbol_strategy_config.get('sell_rule', ''),
                open_rule_expr=symbol_strategy_config.get('open_rule', ''),
                close_rule_expr=symbol_strategy_config.get('close_rule', ''),
                portfolio_manager=engine.portfolio_manager
            )
            engine.register_strategy(rule_strategy)
        elif strategy_type.startswith("规则组:") or strategy_type in ['Martingale', '金叉死叉', '相对强度']:
            self._register_rule_group_strategy(engine, symbol, symbol_data, strategy_type, backtest_config)

    def _register_rule_group_strategy(self, engine, symbol, symbol_data, strategy_type, backtest_config):
        """注册规则组策略"""
        # 处理两种格式: "规则组: Martingale" 或直接 "Martingale"
        if strategy_type.startswith("规则组:"):
            group_name = strategy_type.replace("规则组: ", "")
        else:
            group_name = strategy_type

        print(f"[DEBUG] 尝试注册规则组策略: {strategy_type} -> group_name: {group_name}")

        if 'rule_groups' in self.session_state and group_name in self.session_state.rule_groups:
            group = self.session_state.rule_groups[group_name]

            # 添加调试信息
            print(f"[DEBUG] 注册规则组策略: {group_name}")
            print(f"[DEBUG] 规则内容: {group}")

            rule_strategy = RuleBasedStrategy(
                Data=symbol_data,
                name=f"规则组策略_{symbol}_{group_name}",
                indicator_service=self.session_state.indicator_service,
                buy_rule_expr=group.get('buy_rule', ''),
                sell_rule_expr=group.get('sell_rule', ''),
                open_rule_expr=group.get('open_rule', ''),
                close_rule_expr=group.get('close_rule', ''),
                portfolio_manager=engine.portfolio_manager
            )

            # 验证规则是否正确设置
            print(f"[DEBUG] 策略创建完成: {rule_strategy.name}")
            print(f"[DEBUG] 开仓规则: {rule_strategy.open_rule_expr}")
            print(f"[DEBUG] 清仓规则: {rule_strategy.close_rule_expr}")
            print(f"[DEBUG] 加仓规则: {rule_strategy.buy_rule_expr}")
            print(f"[DEBUG] 平仓规则: {rule_strategy.sell_rule_expr}")

            engine.register_strategy(rule_strategy)
        else:
            print(f"[ERROR] 规则组 '{group_name}' 不存在或 rule_groups 未初始化")
            if 'rule_groups' in self.session_state:
                print(f"[DEBUG] 可用规则组: {list(self.session_state.rule_groups.keys())}")
            else:
                print(f"[DEBUG] session_state 中没有 rule_groups")

    def _register_single_symbol_strategy(self, engine, data, backtest_config):
        """注册单符号策略"""
        default_strategy = backtest_config.default_strategy
        strategy_type = default_strategy.get('type', '使用默认策略')

        if strategy_type == "月定投":
            fixed_strategy = FixedInvestmentStrategy(
                Data=data,
                name="月定投策略",
                buy_rule_expr="True",
                sell_rule_expr="False"
            )
            engine.register_strategy(fixed_strategy)
        elif strategy_type == "自定义规则":
            rule_strategy = RuleBasedStrategy(
                Data=data,
                name="自定义规则策略",
                indicator_service=self.session_state.indicator_service,
                buy_rule_expr=default_strategy.get('buy_rule', ''),
                sell_rule_expr=default_strategy.get('sell_rule', ''),
                open_rule_expr=default_strategy.get('open_rule', ''),
                close_rule_expr=default_strategy.get('close_rule', ''),
                portfolio_manager=engine.portfolio_manager
            )
            engine.register_strategy(rule_strategy)

    async def execute_backtest(self, engine, backtest_config, start_date, end_date):
        """执行回测"""
        task_id = f"backtest_{self.session_state.strategy_id}"

        try:
            if backtest_config.is_multi_symbol():
                # 多符号回测
                engine.run_multi_symbol(pd.to_datetime(start_date), pd.to_datetime(end_date))
            else:
                # 单符号回测
                engine.run(pd.to_datetime(start_date), pd.to_datetime(end_date))

            return engine.get_results()
        except Exception as e:
            logger.error(f"回测执行失败: {str(e)}")
            st.error(f"回测执行失败: {str(e)}")
            return None
        finally:
            progress_service.end_task(task_id)

    def initialize_chart_service(self, data, equity_data):
        """初始化图表服务"""
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
            from src.services.chart_service import DataBundle
            databundle = DataBundle(raw_data, transaction_data, capital_flow_data=None)
            from src.services.chart_service import ChartService
            return ChartService(databundle)

        if 'chart_service' not in self.session_state:
            self.session_state.chart_service = init_chart_service(data, equity_data)
            self.session_state.chart_instance_id = id(self.session_state.chart_service)