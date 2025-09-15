import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from core.strategy.backtesting import BacktestConfig
from core.strategy.strategy import FixedInvestmentStrategy
from core.data.database import DatabaseManager
from services.progress_service import progress_service
from typing import cast
import time
from support.log.logger import logger
import numpy as np

# 导入新创建的模块
from frontend.backtest_config_manager import BacktestConfigManager
from frontend.rule_group_manager import RuleGroupManager
from frontend.strategy_mapping_manager import StrategyMappingManager
from frontend.backtest_executor import BacktestExecutor
from frontend.results_display_manager import ResultsDisplayManager

# 导入新创建的UI组件模块
from frontend.backtest_config_ui import BacktestConfigUI
from frontend.strategy_config_ui import StrategyConfigUI
from frontend.position_config_ui import PositionConfigUI
from frontend.results_display_ui import ResultsDisplayUI

# 导入服务模块
from frontend.data_loader import DataLoader
from frontend.callback_services import CallbackServices
from frontend.event_handlers import EventHandlers

async def show_backtesting_page():
    # 初始化策略ID
    if 'strategy_id' not in st.session_state:
        import uuid
        st.session_state.strategy_id = str(uuid.uuid4())

    # 初始化所有管理器实例
    config_manager = BacktestConfigManager(st.session_state)
    rule_group_manager = RuleGroupManager(st.session_state)
    strategy_mapping_manager = StrategyMappingManager(st.session_state)
    backtest_executor = BacktestExecutor(st.session_state)
    results_display_manager = ResultsDisplayManager(st.session_state)

    # 初始化UI组件
    config_ui = BacktestConfigUI(st.session_state)
    strategy_ui = StrategyConfigUI(st.session_state)
    position_ui = PositionConfigUI(st.session_state)
    results_ui = ResultsDisplayUI(st.session_state)

    # 初始化服务
    data_loader = DataLoader(st.session_state)
    callback_services = CallbackServices(st.session_state)
    event_handlers = EventHandlers(st.session_state)

    # 初始化配置和规则组
    config_manager.initialize_session_config()
    rule_group_manager.initialize_default_rule_groups()
    strategy_mapping_manager.initialize_strategy_mapping()

    st.title("策略回测")

    # 使用标签页组织配置
    config_tab1, config_tab2, config_tab3 = st.tabs(["📊 回测范围", "⚙️ 策略配置", "📈 仓位配置"])

    # 配置标签页1: 回测范围
    with config_tab1:
        config_ui.render_date_config_ui()
        config_ui.render_frequency_config_ui()

        # 使用BacktestConfigUI组件渲染股票选择
        selected_options = config_ui.render_stock_selection_ui()

        # 更新配置对象中的股票代码
        if selected_options:
            selected_symbols = [symbol[0] for symbol in selected_options]
            # 使用统一接口设置符号
            st.session_state.backtest_config.target_symbols = selected_symbols

        # 显示配置摘要
        config_ui.render_config_summary()

    with config_tab2:
        # 使用StrategyConfigUI组件渲染策略配置
        default_strategy_type = strategy_ui.render_strategy_selection_ui()
        strategy_ui.render_custom_rules_ui(rule_group_manager, default_strategy_type)
        strategy_ui.render_multi_symbol_strategy_ui(selected_options, rule_group_manager, config_manager)
        strategy_ui.render_strategy_summary()

    with config_tab3:
        # 使用PositionConfigUI组件渲染仓位配置
        position_ui.render_position_strategy_ui()
        position_ui.render_basic_config_ui()
        position_ui.render_config_summary()
    
    # 初始化按钮状态
    if 'start_backtest_clicked' not in st.session_state:
        st.session_state.start_backtest_clicked = False

    # 带回调的按钮组件
    def on_backtest_click():
        st.session_state.start_backtest_clicked = not st.session_state.start_backtest_clicked

    if st.button(
        "开始回测",
        key="start_backtest",
        on_click=on_backtest_click
    ):
        # 使用存储在session_state中的配置对象
        backtest_config = st.session_state.backtest_config

        # 统一数据加载
        symbols = backtest_config.get_symbols()

        if backtest_config.is_multi_symbol():
            # 多符号模式
            data = await st.session_state.db.load_multiple_stock_data(
                symbols, backtest_config.start_date, backtest_config.end_date, backtest_config.frequency
            )
            st.info(f"已加载 {len(data)} 只股票数据")
        else:
            # 单符号模式
            data = await st.session_state.db.load_stock_data(
                symbols[0], backtest_config.start_date, backtest_config.end_date, backtest_config.frequency
            )

        st.write("回测使用的数据")
        st.write(data)

        # 使用BacktestExecutionService执行回测
        from frontend.backtest_execution_service import BacktestExecutionService
        execution_service = BacktestExecutionService(st.session_state)

        # 初始化引擎
        engine = execution_service.initialize_engine(backtest_config, data)

        # 执行回测
        results = execution_service.execute_backtest(engine, backtest_config)

        # 处理多符号和单符号的净值数据
        if "combined_equity" in results:
            # 多符号模式
            equity_data = results["combined_equity"]
            if "individual" in results:
                individual_results = results["individual"]
        else:
            # 单符号模式
            equity_data = pd.DataFrame(results["equity_records"])

        # 准备图表服务
        execution_service.prepare_chart_service(data, equity_data)

        if results:
            st.success("回测完成！")
            
            # 使用ResultsDisplayUI组件显示结果
            results_ui.render_results_tabs(results, backtest_config)
        else:
            st.error("回测失败，请检查输入参数")
