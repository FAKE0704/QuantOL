import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from src.core.strategy.backtesting import BacktestConfig
from src.core.strategy.strategy import FixedInvestmentStrategy
from src.core.data.database import DatabaseManager
from src.services.progress_service import progress_service
from typing import cast
import time
from src.support.log.logger import logger
import numpy as np

# 导入新创建的模块
from src.frontend.backtest_config_manager import BacktestConfigManager
from src.frontend.rule_group_manager import RuleGroupManager
from src.frontend.strategy_mapping_manager import StrategyMappingManager
from src.frontend.results_display_manager import ResultsDisplayManager
from src.frontend.backtest_execution_service import BacktestExecutionService

# 导入新创建的UI组件模块
from src.frontend.backtest_config_ui import BacktestConfigUI
from src.frontend.strategy_config_ui import StrategyConfigUI
from src.frontend.position_config_ui import PositionConfigUI
from src.frontend.results_display_ui import ResultsDisplayUI

# 导入新的自适应策略配置UI
from src.frontend.strategy_config import AdaptiveStrategyConfigUI

# 导入服务模块
from src.frontend.data_loader import DataLoader
from src.frontend.callback_services import CallbackServices
from src.frontend.event_handlers import EventHandlers

# 导入配置持久化模块
from src.frontend.backtest_config_persistence import BacktestConfigPersistence
from src.frontend.backtest_config_persistence_ui import BacktestConfigPersistenceUI

async def show_backtesting_page():
    # 初始化策略ID
    if 'strategy_id' not in st.session_state:
        import uuid
        st.session_state.strategy_id = str(uuid.uuid4())

    # 初始化所有管理器实例
    config_manager = BacktestConfigManager(st.session_state)
    rule_group_manager = RuleGroupManager(st.session_state)
    strategy_mapping_manager = StrategyMappingManager(st.session_state)
    backtest_execution_service = BacktestExecutionService(st.session_state)
    results_display_manager = ResultsDisplayManager(st.session_state)

    # 初始化UI组件
    config_ui = BacktestConfigUI(st.session_state)
    strategy_ui = StrategyConfigUI(st.session_state)
    position_ui = PositionConfigUI(st.session_state)
    results_ui = ResultsDisplayUI(st.session_state)

    # 初始化新的自适应策略配置UI
    adaptive_strategy_ui = AdaptiveStrategyConfigUI(st.session_state)

    # 初始化服务
    data_loader = DataLoader(st.session_state)
    callback_services = CallbackServices(st.session_state)
    event_handlers = EventHandlers(st.session_state)

    # 初始化配置持久化管理器和UI
    persistence_manager = BacktestConfigPersistence()
    persistence_ui = BacktestConfigPersistenceUI(st.session_state, persistence_manager)

    # 初始化配置和规则组
    config_manager.initialize_session_config()
    rule_group_manager.initialize_default_rule_groups()
    strategy_mapping_manager.initialize_strategy_mapping()

    st.title("策略回测")

    # 检测并应用待加载的配置（必须在render_date_config_ui之前执行）
    if st.session_state.get('pending_load_config'):
        pending_config = st.session_state.pending_load_config
        logger.info(f"[加载配置] 待加载配置: target_symbol={pending_config.target_symbol}, target_symbols={pending_config.target_symbols}, strategy_type={pending_config.strategy_type}")

        # 清除旧的标的相关的 session_state 键（避免验证时检查到旧标的）
        old_symbols = [k.replace('_has_custom_config', '') for k in st.session_state.keys()
                      if k.endswith('_has_custom_config')]
        for old_symbol in old_symbols:
            if old_symbol not in pending_config.target_symbols:
                logger.info(f"[加载配置] 清除旧标的 session_state: {old_symbol}")
                # 清除旧标的策略类型和规则相关键
                keys_to_remove = [k for k in st.session_state.keys()
                                   if k.startswith(f'strategy_type_{old_symbol}') or
                                      k.startswith(f'open_rule_{old_symbol}') or
                                      k.startswith(f'close_rule_{old_symbol}') or
                                      k.startswith(f'buy_rule_{old_symbol}') or
                                      k.startswith(f'sell_rule_{old_symbol}') or
                                      k == f'{old_symbol}_has_custom_config']
                for key in keys_to_remove:
                    del st.session_state[key]

        st.session_state.backtest_config = pending_config

        # 改变 widget key 后缀，强制创建新实例
        import time
        key_suffix = int(time.time() * 1000)
        st.session_state._date_key_suffix = key_suffix
        st.session_state._stock_key_suffix = key_suffix  # 股票选择也使用相同后缀
        st.session_state._frequency_key_suffix = key_suffix  # 频率配置
        st.session_state._position_key_suffix = key_suffix  # 仓位管理
        st.session_state._basic_config_key_suffix = key_suffix  # 基础配置

        # 设置临时标记，用于初始化新值
        st.session_state._load_start_date = pending_config.start_date
        st.session_state._load_end_date = pending_config.end_date
        st.session_state._load_symbols = pending_config.target_symbols  # 加载股票列表
        st.session_state._load_frequency = pending_config.frequency  # 加载数据频率
        st.session_state._load_position_strategy = pending_config.position_strategy_type  # 加载仓位策略类型

        # 同步策略类型到 session_state
        for symbol in pending_config.target_symbols:
            st.session_state[f"strategy_type_{symbol}"] = pending_config.strategy_type
            # 设置 has_custom_config 标记
            st.session_state[f"{symbol}_has_custom_config"] = True
            # 如果是自定义规则，同步规则
            if pending_config.strategy_type == "自定义规则" and pending_config.custom_rules:
                st.session_state[f"open_rule_{symbol}"] = pending_config.custom_rules.get('open_rule', '')
                st.session_state[f"close_rule_{symbol}"] = pending_config.custom_rules.get('close_rule', '')
                st.session_state[f"buy_rule_{symbol}"] = pending_config.custom_rules.get('buy_rule', '')
                st.session_state[f"sell_rule_{symbol}"] = pending_config.custom_rules.get('sell_rule', '')

        # 设置策略 key 后缀，强制刷新策略选择 UI
        st.session_state._strategy_key_suffix = key_suffix

        logger.info(f"[加载配置] 已同步策略类型到 session_state, 设置 _strategy_key_suffix={key_suffix}")

        # 清除待加载配置标记并设置成功消息标记
        st.session_state.pending_load_config = None
        st.session_state.config_loaded_success = True

    # 使用标签页组织配置
    config_tab1, config_tab2, config_tab3 = st.tabs(["📊 回测范围", "⚙️ 策略配置", "📈 仓位配置"])

    # 配置标签页1: 回测范围
    with config_tab1:
        # 显示配置加载成功消息
        if st.session_state.get('config_loaded_success', False):
            st.success("✅ 配置已加载，所有参数已更新")
            st.session_state.config_loaded_success = False

        config_ui.render_date_config_ui()
        config_ui.render_frequency_config_ui()

        # 使用BacktestConfigUI组件渲染股票选择
        selected_options = await config_ui.render_stock_selection_ui()

        # 更新配置对象中的股票代码
        if selected_options:
            selected_symbols = [symbol[0] for symbol in selected_options]
            # 使用统一接口设置符号（同时更新 target_symbol 和 target_symbols）
            st.session_state.backtest_config.target_symbols = selected_symbols
            st.session_state.backtest_config.target_symbol = selected_symbols[0] if selected_symbols else ""

        # 显示配置摘要
        config_ui.render_config_summary()

    with config_tab2:
        # 使用新的自适应策略配置UI
        adaptive_strategy_ui.render_configuration(selected_options, rule_group_manager, config_manager)
        adaptive_strategy_ui.render_strategy_summary()

    with config_tab3:
        # 使用PositionConfigUI组件渲染仓位配置
        position_ui.render_position_strategy_ui()
        position_ui.render_basic_config_ui()
        position_ui.render_config_summary()

    # 配置管理区域
    st.markdown("---")

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("💾 保存配置", key="save_config_btn"):
            st.session_state.show_save_dialog = True
    with col2:
        if st.button("📂 加载配置", key="load_config_btn"):
            st.session_state.show_load_panel = True
    with col3:
        if st.button("📋 配置管理", key="config_manage_btn"):
            st.session_state.show_management_panel = not st.session_state.get('show_management_panel', False)

    # 保存配置对话框
    if st.session_state.get('show_save_dialog', False):
        with st.expander("💾 保存当前配置", expanded=True):
            # 保存前先同步策略配置
            adaptive_strategy_ui.sync_config_with_backtest_config(st.session_state.backtest_config)

            if persistence_ui.render_save_config_dialog(st.session_state.backtest_config):
                st.success("配置保存成功！")
                st.session_state.show_save_dialog = False
                st.rerun()

            if st.button("关闭", key="close_save_dialog"):
                st.session_state.show_save_dialog = False
                st.rerun()

    # 加载配置面板
    if st.session_state.get('show_load_panel', False):
        with st.expander("📂 加载已保存配置", expanded=True):
            loaded_config = persistence_ui.render_load_config_ui()
            if loaded_config:
                # 不直接更新配置，而是存入待加载队列
                # 这样会在下次渲染时（在render_date_config_ui之前）应用
                st.session_state.pending_load_config = loaded_config
                st.session_state.show_load_panel = False
                st.rerun()

            if st.button("关闭", key="close_load_panel"):
                st.session_state.show_load_panel = False
                st.rerun()

    # 配置管理面板
    if st.session_state.get('show_management_panel', False):
        with st.expander("📋 配置管理", expanded=True):
            current_user = st.session_state.get('current_user')
            if current_user:
                persistence_ui.render_config_management_panel(current_user['username'])
            else:
                st.error("请先登录")

            if st.button("关闭管理面板", key="close_management_panel"):
                st.session_state.show_management_panel = False
                st.rerun()

    st.markdown("---")

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
        # 验证策略配置
        is_valid, error_msg = adaptive_strategy_ui.validate_configuration()
        if not is_valid:
            st.error(f"❌ 配置验证失败: {error_msg}")
            return

        # 同步UI配置到回测配置对象
        backtest_config = st.session_state.backtest_config
        adaptive_strategy_ui.sync_config_with_backtest_config(backtest_config)

        st.success("✅ 配置验证通过，开始执行回测...")

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
        execution_service = backtest_execution_service

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

            # 保存结果到 session_state，避免 rerun 时丢失
            st.session_state.backtest_results = results
            st.session_state.last_backtest_config = backtest_config
            st.session_state.equity_data = equity_data
            st.rerun()  # 触发 rerun 以显示结果
        else:
            st.error("回测失败，请检查输入参数")

    # 显示已保存的回测结果（在按钮外，避免 rerun 时丢失）
    if 'backtest_results' in st.session_state and st.session_state.backtest_results:
        st.markdown("---")
        st.info("📋 显示最近一次回测结果")

        results = st.session_state.backtest_results
        backtest_config = st.session_state.last_backtest_config
        equity_data = st.session_state.equity_data

        # 准备图表服务
        execution_service = backtest_execution_service
        if equity_data is not None and not equity_data.empty:
            execution_service.prepare_chart_service(None, equity_data)

        # 使用ResultsDisplayUI组件显示结果
        results_ui.render_results_tabs(results, backtest_config)
