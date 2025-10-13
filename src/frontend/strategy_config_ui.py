import streamlit as st
from typing import List, Tuple
from frontend.rule_group_manager import RuleGroupManager
from frontend.strategy_mapping_manager import StrategyMappingManager
from frontend.backtest_config_manager import BacktestConfigManager

class StrategyConfigUI:
    """策略配置UI组件，负责策略相关配置的界面渲染"""

    def __init__(self, session_state):
        self.session_state = session_state

    def render_strategy_selection_ui(self) -> str:
        """渲染策略选择UI，返回选中的策略类型"""
        st.subheader("🎯 选择策略类型")

        default_strategy_type = st.selectbox(
            "默认策略类型",
            options=["月定投", "移动平均线交叉", "MACD交叉", "RSI超买超卖", "自定义规则"],
            key="default_strategy_type"
        )

        return default_strategy_type

    def render_custom_rules_ui(self, rule_group_manager: RuleGroupManager, strategy_type: str) -> None:
        """渲染自定义规则UI"""
        if strategy_type == "自定义规则":
            st.subheader("⚙️ 自定义交易规则")

            # 规则组管理
            rule_group_manager.render_rule_group_management_ui()

            # 规则编辑器
            col1, col2 = st.columns(2)
            with col1:
                rule_group_manager.render_rule_editor_ui('buy_rule', "", "default", 60)
                rule_group_manager.render_rule_editor_ui('sell_rule', "", "default", 60)
            with col2:
                rule_group_manager.render_rule_editor_ui('open_rule', "", "default", 60)
                rule_group_manager.render_rule_editor_ui('close_rule', "", "default", 60)

    def render_multi_symbol_strategy_ui(self,
                                      selected_options: List[Tuple[str, str]],
                                      rule_group_manager: RuleGroupManager,
                                      config_manager: BacktestConfigManager) -> None:
        """渲染多股票策略配置UI"""
        if len(selected_options) > 1:
            st.subheader("🔀 多股票策略配置")

            # 使用策略映射管理器
            strategy_mapping_manager = StrategyMappingManager(self.session_state)
            strategy_mapping_manager.render_multi_symbol_strategy_ui(
                selected_options, rule_group_manager, config_manager
            )

    def render_strategy_summary(self) -> None:
        """渲染策略配置摘要"""
        config = self.session_state.backtest_config

        st.subheader("📋 策略配置摘要")

        # 显示策略类型
        strategy_type = getattr(config, 'strategy_type', '月定投')
        st.info(f"**策略类型**: {strategy_type}")

        # 显示仓位策略
        position_strategy = getattr(config, 'position_strategy_type', 'fixed_percent')
        position_map = {
            'fixed_percent': '固定比例',
            'kelly': '凯利公式',
            'martingale': '马丁格尔'
        }
        st.info(f"**仓位策略**: {position_map.get(position_strategy, position_strategy)}")

        # 如果是多股票模式，显示策略映射信息
        if hasattr(config, 'strategy_mapping') and config.strategy_mapping:
            st.info(f"**策略映射**: {len(config.strategy_mapping)} 个自定义配置")