"""
自适应策略配置UI组件
根据选择的标的数量动态切换配置界面
"""
import streamlit as st
from typing import List, Tuple, Optional
from .single_asset_config_ui import SingleAssetConfigUI
from .multi_asset_config_ui import MultiAssetConfigUI
from .strategy_inheritance_manager import StrategyInheritanceManager


class AdaptiveStrategyConfigUI:
    """自适应策略配置UI控制器"""

    def __init__(self, session_state):
        self.session_state = session_state
        self.single_asset_ui = SingleAssetConfigUI(session_state)
        self.multi_asset_ui = MultiAssetConfigUI(session_state)
        self.inheritance_manager = StrategyInheritanceManager(session_state)

    def render_configuration(self, selected_options: List[Tuple[str, str]],
                           rule_group_manager, config_manager):
        """
        根据选择的标的数量渲染相应的配置界面

        Args:
            selected_options: 选择的标的列表 [(symbol, name), ...]
            rule_group_manager: 规则组管理器
            config_manager: 配置管理器
        """
        asset_count = len(selected_options)

        # 根据标的数量确定配置模式
        mode = self._determine_configuration_mode(asset_count)

        # 保存当前配置模式到session state
        self.session_state.strategy_config_mode = mode

        if mode == 'empty':
            self._render_empty_state()
        elif mode == 'single':
            self._render_single_asset_mode(selected_options, rule_group_manager, config_manager)
        elif mode == 'multi':
            self._render_multi_asset_mode(selected_options, rule_group_manager, config_manager)

    def _determine_configuration_mode(self, asset_count: int) -> str:
        """
        根据标的数量确定配置模式

        Args:
            asset_count: 标的数量

        Returns:
            配置模式: 'empty', 'single', 'multi'
        """
        if asset_count == 0:
            return 'empty'
        elif asset_count == 1:
            return 'single'
        else:
            return 'multi'

    def _render_empty_state(self):
        """渲染空状态界面"""
        st.warning("⚠️ 请先选择至少一个标的来配置策略")
        st.info("💡 **提示**: 在左侧的'回测范围'标签页中选择您要回测的股票标的")

    def _render_single_asset_mode(self, selected_options: List[Tuple[str, str]],
                                rule_group_manager, config_manager):
        """
        渲染单标模式配置界面

        Args:
            selected_options: 选择的标的列表
            rule_group_manager: 规则组管理器
            config_manager: 配置管理器
        """
        st.subheader("🎯 单标策略配置")
        st.info(f"当前配置标的: **{selected_options[0][1]} ({selected_options[0][0]})**")

        # 使用单标配置UI组件
        self.single_asset_ui.render_configuration(selected_options[0], rule_group_manager, config_manager)

    def _render_multi_asset_mode(self, selected_options: List[Tuple[str, str]],
                               rule_group_manager, config_manager):
        """
        渲染多标模式配置界面

        Args:
            selected_options: 选择的标的列表
            rule_group_manager: 规则组管理器
            config_manager: 配置管理器
        """
        st.subheader("🎯 多标策略配置")
        st.info(f"当前配置 {len(selected_options)} 个标的，可为每个标的单独配置策略或使用全局默认设置")

        # 使用多标配置UI组件
        self.multi_asset_ui.render_configuration(selected_options, rule_group_manager, config_manager)

    def get_strategy_summary(self) -> dict:
        """
        获取当前策略配置摘要

        Returns:
            策略配置摘要字典
        """
        mode = self.session_state.get('strategy_config_mode', 'empty')

        if mode == 'single':
            return self.single_asset_ui.get_strategy_summary()
        elif mode == 'multi':
            return self.multi_asset_ui.get_strategy_summary()
        else:
            return {'mode': 'empty', 'message': '未配置策略'}

    def validate_configuration(self) -> tuple[bool, str]:
        """
        验证当前配置的合法性

        Returns:
            (is_valid, error_message): 验证结果和错误信息
        """
        mode = self.session_state.get('strategy_config_mode', 'empty')

        if mode == 'empty':
            return False, "请先选择至少一个标的"

        # 验证策略继承关系
        is_valid, error_msg = self.inheritance_manager.validate_strategy_hierarchy()

        if not is_valid:
            return False, f"策略配置验证失败: {error_msg}"

        return True, "配置验证通过"

    def get_effective_strategies(self, backtest_config) -> dict:
        """
        获取所有标的的有效策略配置

        Args:
            backtest_config: 回测配置对象

        Returns:
            每个标的的有效策略配置
        """
        mode = self.session_state.get('strategy_config_mode', 'empty')

        if mode == 'single':
            # 单标模式直接返回配置
            return {'single': backtest_config}
        elif mode == 'multi':
            # 多标模式需要处理策略继承
            return self.inheritance_manager.get_effective_strategies(backtest_config)
        else:
            return {}

    def render_strategy_summary(self):
        """渲染策略配置摘要"""
        summary = self.get_strategy_summary()

        st.subheader("📋 策略配置摘要")

        if summary.get('mode') == 'empty':
            st.warning("未配置策略")
        elif summary.get('mode') == 'single':
            # 显示单标配置摘要
            st.info(f"**配置模式**: 单标策略")
            st.info(f"**策略类型**: {summary.get('strategy_type', '未设置')}")
            if summary.get('custom_rules'):
                st.info(f"**自定义规则**: 已配置")
        elif summary.get('mode') == 'multi':
            # 显示多标配置摘要
            st.info(f"**配置模式**: 多标策略")
            st.info(f"**全局默认策略**: {summary.get('global_strategy_type', '未设置')}")

            individual_configs = summary.get('individual_configs', {})
            custom_count = len([c for c in individual_configs.values() if c.get('use_custom')])
            default_count = len(individual_configs) - custom_count

            st.info(f"**个别配置**: {custom_count} 个自定义策略, {default_count} 个使用默认")

    def sync_config_with_backtest_config(self, backtest_config):
        """
        同步UI配置到回测配置对象

        Args:
            backtest_config: 回测配置对象
        """
        mode = self.session_state.get('strategy_config_mode', 'empty')

        if mode == 'single':
            self.single_asset_ui.sync_config_with_backtest_config(backtest_config)
        elif mode == 'multi':
            self.multi_asset_ui.sync_config_with_backtest_config(backtest_config)

        # 同步策略继承信息
        backtest_config.strategy_inheritance = self.inheritance_manager.get_inheritance_rules()