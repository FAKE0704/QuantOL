"""
多标策略配置UI组件
处理多个标的的策略配置界面
"""
import streamlit as st
from typing import List, Tuple, Dict, Any


class MultiAssetConfigUI:
    """多标策略配置UI组件"""

    def __init__(self, session_state):
        self.session_state = session_state

    def render_configuration(self, selected_options: List[Tuple[str, str]],
                           rule_group_manager, config_manager):
        """
        渲染多标策略配置界面

        Args:
            selected_options: 选择的标的列表 [(symbol, name), ...]
            rule_group_manager: 规则组管理器
            config_manager: 配置管理器
        """
        # 全局默认设置（暂时注释掉）
        # self._render_global_default_settings(selected_options, rule_group_manager)

        # 删除批量操作工具栏
        # self._render_batch_operations(selected_options, rule_group_manager)

        # 个别标的配置
        self._render_individual_asset_configurations(selected_options, rule_group_manager)

        # 配置摘要
        self._render_configuration_summary(selected_options)

    def _render_global_default_settings(self, selected_options: List[Tuple[str, str]],
                                       rule_group_manager):
        """
        渲染全局默认设置

        Args:
            selected_options: 选择的标的列表
            rule_group_manager: 规则组管理器
        """
        with st.expander("🌐 全局默认设置", expanded=False):
            st.write("设置所有标的的默认策略配置，个别标的可以覆盖这些设置")

            # 全局策略类型
            global_strategy_type = st.selectbox(
                "全局默认策略类型",
                options=["月定投", "移动平均线交叉", "MACD交叉", "RSI超买超卖", "自定义规则"],
                key="global_default_strategy_type",
                help="所有标的的默认策略类型（可以被个别配置覆盖）"
            )

            # 全局自定义规则（如果选择了自定义规则）
            if global_strategy_type == "自定义规则":
                self._render_global_custom_rules(rule_group_manager)

            # 应用到所有按钮
            if st.button("🔄 应用全局设置到所有标的", key="apply_global_to_all"):
                self._apply_global_settings_to_all(selected_options, global_strategy_type, rule_group_manager)
                st.success("✅ 全局设置已应用到所有标的")

    def _render_global_custom_rules(self, rule_group_manager):
        """渲染全局自定义规则设置"""
        st.write("**全局默认自定义规则**")

        # 预定义规则组加载区域
        self._render_global_rule_group_loader(rule_group_manager)

        st.divider()  # 分割线

        # 手动配置全局规则区域
        st.write("**手动配置全局默认规则**")
        st.info("💡 您可以直接在下方编辑全局默认规则，或者先加载预定义规则组后进行修改")

        # 快速操作按钮
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("🧹 清空所有全局规则", key="clear_global_rules"):
                self._clear_global_rules()
                st.success("✅ 已清空所有全局默认规则")

        with col2:
            if st.button("📋 填充示例规则", key="fill_global_example"):
                self._fill_global_example_rules()
                st.success("✅ 已填充示例规则")

        # 规则编辑器
        rule_col1, rule_col2 = st.columns(2)

        # 获取当前全局规则值
        global_open_rule = self.session_state.get("global_open_rule", "")
        global_close_rule = self.session_state.get("global_close_rule", "")
        global_buy_rule = self.session_state.get("global_buy_rule", "")
        global_sell_rule = self.session_state.get("global_sell_rule", "")

        with rule_col1:
            global_open_rule_value = st.text_area(
                "全局默认开仓条件",
                value=global_open_rule,
                height=80,
                key="global_open_rule_widget",
                help="所有标的的默认开仓条件"
            )
            # 手动同步到session_state
            if global_open_rule_value != global_open_rule:
                self.session_state["global_open_rule"] = global_open_rule_value

            global_close_rule_value = st.text_area(
                "全局默认清仓条件",
                value=global_close_rule,
                height=80,
                key="global_close_rule_widget",
                help="所有标的的默认清仓条件"
            )
            # 手动同步到session_state
            if global_close_rule_value != global_close_rule:
                self.session_state["global_close_rule"] = global_close_rule_value

        with rule_col2:
            global_buy_rule_value = st.text_area(
                "全局默认加仓条件",
                value=global_buy_rule,
                height=80,
                key="global_buy_rule_widget",
                help="所有标的的默认加仓条件"
            )
            # 手动同步到session_state
            if global_buy_rule_value != global_buy_rule:
                self.session_state["global_buy_rule"] = global_buy_rule_value

            global_sell_rule_value = st.text_area(
                "全局默认平仓条件",
                value=global_sell_rule,
                height=80,
                key="global_sell_rule_widget",
                help="所有标的的默认平仓条件"
            )
            # 手动同步到session_state
            if global_sell_rule_value != global_sell_rule:
                self.session_state["global_sell_rule"] = global_sell_rule_value

        # 规则编写帮助按钮
        if st.button("📖 规则编写帮助", key="help_global_rules"):
            self._show_rules_help_modal()

    def _render_global_rule_group_loader(self, rule_group_manager):
        """
        渲染全局规则组加载区域

        Args:
            rule_group_manager: 规则组管理器
        """
        # 获取可用的规则组
        rule_groups = rule_group_manager.get_rule_options_for_display()

        if rule_groups:
            st.write("**📦 加载全局预定义规则组**")

            # 使用columns布局，左侧选择框，右侧按钮
            col1, col2 = st.columns([3, 1])

            with col1:
                selected_global_group = st.selectbox(
                    "选择全局预定义规则组",
                    options=["请选择规则组"] + rule_groups,
                    key="global_rule_group",
                    help="选择要加载为全局默认的预定义规则组"
                )

            with col2:
                # 将按钮垂直居中对齐
                st.markdown("<br>", unsafe_allow_html=True)  # 添加一些间距
                load_button_disabled = selected_global_group == "请选择规则组"
                if st.button(
                    f"🔄 加载规则组",
                    key="load_global_group",
                    disabled=load_button_disabled,
                    help="加载选择的规则组为全局默认规则"
                ):
                    if selected_global_group != "请选择规则组":
                        self._apply_global_rule_group(selected_global_group, rule_group_manager)
                        st.success(f"✅ 已加载规则组 '{selected_global_group}' 为全局默认规则")
                        # st.rerun() 现在在 _apply_global_rule_group 中调用

            # 显示规则组预览（当选择了规则组时）
            if selected_global_group != "请选择规则组":
                group = rule_group_manager.get_rule_group(selected_global_group)
                if group:
                    with st.expander(f"👀 预览全局规则组: {selected_global_group}", expanded=False):
                        col1, col2 = st.columns(2)
                        with col1:
                            if group.get('open_rule'):
                                st.code(f"开仓: {group['open_rule']}")
                            if group.get('close_rule'):
                                st.code(f"清仓: {group['close_rule']}")
                        with col2:
                            if group.get('buy_rule'):
                                st.code(f"加仓: {group['buy_rule']}")
                            if group.get('sell_rule'):
                                st.code(f"平仓: {group['sell_rule']}")
        else:
            st.warning("⚠️ 暂无可用规则组，请先在规则组管理中创建")

    def _render_batch_operations(self, selected_options: List[Tuple[str, str]], rule_group_manager):
        """
        渲染批量操作工具栏

        Args:
            selected_options: 选择的标的列表
            rule_group_manager: 规则组管理器
        """
        st.subheader("🛠️ 批量操作工具")

        col1, col2 = st.columns(2)

        with col1:
            # 复制配置
            if len(selected_options) > 1:
                st.markdown("**📋 复制配置**")
                source_symbols = [opt[0] for opt in selected_options]
                source_symbol = st.selectbox(
                    "复制配置来源",
                    options=source_symbols,
                    key="copy_config_source",
                    help="选择一个标的作为配置来源"
                )

                target_symbols = st.multiselect(
                    "复制到标的",
                    options=[s for s in source_symbols if s != source_symbol],
                    key="copy_config_targets",
                    help="选择要复制配置的目标标的"
                )

                if st.button("📋 复制配置", key="copy_config_button"):
                    if target_symbols:
                        self._copy_config_to_targets(source_symbol, target_symbols)
                        st.success(f"✅ 配置已从 {source_symbol} 复制到 {', '.join(target_symbols)}")
                    else:
                        st.warning("⚠️ 请选择至少一个目标标的")

        with col2:
            # 批量设置策略类型
            st.markdown("**⚡ 批量设置策略**")
            batch_strategy_type = st.selectbox(
                "批量设置策略类型",
                options=["不设置", "月定投", "移动平均线交叉", "MACD交叉", "RSI超买超卖", "自定义规则"],
                key="batch_strategy_type"
            )

            if batch_strategy_type != "不设置":
                if st.button("⚡ 应用策略类型", key="batch_apply_strategy"):
                    self._batch_apply_strategy_type(selected_options, batch_strategy_type)
                    st.success(f"✅ 已将策略类型设置为 '{batch_strategy_type}'")

        # 清空所有配置
        st.markdown("**🧹 清空操作**")
        if st.button("🧹 清空所有标的配置", key="reset_all_individual"):
            self._reset_all_individual_configs(selected_options)
            st.success("✅ 所有个别配置已清空")

    def _render_individual_asset_configurations(self, selected_options: List[Tuple[str, str]], rule_group_manager):
        """
        渲染个别标的的配置界面

        Args:
            selected_options: 选择的标的列表
            rule_group_manager: 规则组管理器
        """
        st.subheader("📊 个别标的配置")

        for symbol, name in selected_options:
            # 为每个标的创建可折叠的配置区域
            with st.expander(f"🔧 {symbol} - {name}", expanded=False):
                config_status = self._get_asset_config_status(symbol)
                self._render_single_asset_config(symbol, name, rule_group_manager, config_status)

    def _render_single_asset_config(self, symbol: str, name: str, rule_group_manager, config_status: Dict[str, Any]):
        """
        渲染单个标的的配置界面

        Args:
            symbol: 标的代码
            name: 标的名称
            rule_group_manager: 规则组管理器
            config_status: 配置状态
        """
        # 启用自定义策略配置
        self.session_state[f"{symbol}_has_custom_config"] = True

        # 策略类型选择
        strategy_type = st.selectbox(
            f"策略类型 - {symbol}",
            options=["月定投", "移动平均线交叉", "MACD交叉", "RSI超买超卖", "自定义规则"],
            key=f"strategy_type_{symbol}"
        )

        # 自定义规则（如果选择了自定义规则）
        if strategy_type == "自定义规则":
            self._render_asset_custom_rules(symbol, rule_group_manager)

        # 快速操作按钮
        col1, col2 = st.columns(2)
        with col1:
            if st.button(f"📋 复制全局规则", key=f"copy_global_rules_{symbol}"):
                self._copy_global_rules_to_asset(symbol)
                st.success(f"✅ 已复制全局规则到 {symbol}")

        with col2:
            if st.button(f"🔄 重置为全局默认", key=f"reset_to_global_{symbol}"):
                self._reset_asset_to_global(symbol)
                st.success(f"✅ {symbol} 已重置为全局默认")

    def _render_asset_custom_rules(self, symbol: str, rule_group_manager):
        """
        渲染标的的自定义规则配置

        Args:
            symbol: 标的代码
            rule_group_manager: 规则组管理器
        """
        st.write(f"**自定义交易规则 - {symbol}**")

        # 预定义规则组加载区域
        self._render_asset_rule_group_loader(symbol, rule_group_manager)

        st.divider()  # 分割线

        # 手动配置规则区域
        st.write(f"**手动配置交易规则 - {symbol}**")
        st.info("💡 您可以直接在下方编辑规则，或者先加载预定义规则组后进行修改")

        # 快速操作按钮
        col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
        with col1:
            if st.button(f"📋 从全局默认复制", key=f"copy_global_{symbol}"):
                self._copy_global_rules_to_asset(symbol)
                st.success(f"✅ 已从全局默认规则复制到 {symbol}")

        with col2:
            if st.button(f"🧹 清空所有规则", key=f"clear_rules_{symbol}"):
                self._clear_asset_rules(symbol)
                st.success(f"✅ 已清空 {symbol} 的所有规则")

        with col3:
            if st.button(f"📤 导出规则配置", key=f"export_rules_{symbol}"):
                self._export_rules_to_json(symbol)

        with col4:
            if st.button(f"📥 导入规则配置", key=f"import_rules_{symbol}"):
                self._import_rules_from_json(symbol)

        # 规则编辑器
        rule_editor_col1, rule_editor_col2 = st.columns(2)

        # 获取当前规则值
        open_rule = self.session_state.get(f"open_rule_{symbol}", "")
        close_rule = self.session_state.get(f"close_rule_{symbol}", "")
        buy_rule = self.session_state.get(f"buy_rule_{symbol}", "")
        sell_rule = self.session_state.get(f"sell_rule_{symbol}", "")

        with rule_editor_col1:
            open_rule_value = st.text_area(
                "开仓条件",
                value=open_rule,
                height=80,
                key=f"open_rule_{symbol}_widget",
                help="输入开仓条件表达式，例如: close > ma20"
            )
            # 手动同步到session_state
            if open_rule_value != open_rule:
                self.session_state[f"open_rule_{symbol}"] = open_rule_value

            close_rule_value = st.text_area(
                "清仓条件",
                value=close_rule,
                height=80,
                key=f"close_rule_{symbol}_widget",
                help="输入清仓条件表达式，例如: close < ma20"
            )
            # 手动同步到session_state
            if close_rule_value != close_rule:
                self.session_state[f"close_rule_{symbol}"] = close_rule_value

        with rule_editor_col2:
            buy_rule_value = st.text_area(
                "加仓条件",
                value=buy_rule,
                height=80,
                key=f"buy_rule_{symbol}_widget",
                help="输入加仓条件表达式，例如: rsi < 30"
            )
            # 手动同步到session_state
            if buy_rule_value != buy_rule:
                self.session_state[f"buy_rule_{symbol}"] = buy_rule_value

            sell_rule_value = st.text_area(
                "平仓条件",
                value=sell_rule,
                height=80,
                key=f"sell_rule_{symbol}_widget",
                help="输入平仓条件表达式，例如: rsi > 70"
            )
            # 手动同步到session_state
            if sell_rule_value != sell_rule:
                self.session_state[f"sell_rule_{symbol}"] = sell_rule_value

        # 规则编写帮助按钮
        if st.button(f"📖 规则编写帮助", key=f"help_rules_{symbol}"):
            self._show_rules_help_modal()

    def _render_asset_rule_group_loader(self, symbol: str, rule_group_manager):
        """
        渲染单个标的的规则组加载区域

        Args:
            symbol: 标的代码
            rule_group_manager: 规则组管理器
        """
        # 获取可用的规则组
        rule_groups = rule_group_manager.get_rule_options_for_display()

        if rule_groups:
            st.write(f"**📦 加载预定义规则组 - {symbol}**")

            # 使用columns布局，左侧选择框，右侧按钮
            col1, col2 = st.columns([3, 1])

            with col1:
                selected_group = st.selectbox(
                    "选择预定义规则组",
                    options=["请选择规则组"] + rule_groups,
                    key=f"selected_rule_group_{symbol}",
                    help="选择要加载的预定义规则组"
                )

            with col2:
                # 将按钮垂直居中对齐
                st.markdown("<br>", unsafe_allow_html=True)  # 添加一些间距
                load_button_disabled = selected_group == "请选择规则组"
                if st.button(
                    f"🔄 加载规则组",
                    key=f"load_group_{symbol}",
                    disabled=load_button_disabled,
                    help="加载选择的规则组到下方编辑器中"
                ):
                    if selected_group != "请选择规则组":
                        self._apply_rule_group_to_asset(symbol, selected_group, rule_group_manager)
                        st.success(f"✅ 已加载规则组 '{selected_group}' 到 {symbol} 的编辑器中")
                        # st.rerun() 现在在 _apply_rule_group_to_asset 中调用

            # 显示规则组预览（当选择了规则组时）
            if selected_group != "请选择规则组":
                group = rule_group_manager.get_rule_group(selected_group)
                if group:
                    with st.expander(f"👀 预览规则组: {selected_group}", expanded=False):
                        col1, col2 = st.columns(2)
                        with col1:
                            if group.get('open_rule'):
                                st.code(f"开仓: {group['open_rule']}")
                            if group.get('close_rule'):
                                st.code(f"清仓: {group['close_rule']}")
                        with col2:
                            if group.get('buy_rule'):
                                st.code(f"加仓: {group['buy_rule']}")
                            if group.get('sell_rule'):
                                st.code(f"平仓: {group['sell_rule']}")
        else:
            st.warning("⚠️ 暂无可用规则组，请先在规则组管理中创建")

    def _render_configuration_summary(self, selected_options: List[Tuple[str, str]]):
        """
        渲染配置摘要

        Args:
            selected_options: 选择的标的列表
        """
        st.subheader("📋 配置摘要")

        # 个别配置统计
        configured_count = 0
        unconfigured_count = 0

        strategy_types = {}

        for symbol, name in selected_options:
            if self.session_state.get(f"{symbol}_has_custom_config", False):
                configured_count += 1
                strategy_type = self.session_state.get(f"strategy_type_{symbol}", "未设置")
                strategy_types[strategy_type] = strategy_types.get(strategy_type, 0) + 1
            else:
                unconfigured_count += 1

        # 显示统计信息
        st.info(f"**配置统计**: {configured_count} 个已配置, {unconfigured_count} 个未配置")

        # 显示策略类型分布
        if strategy_types:
            st.info("**策略类型分布**:")
            for strategy_type, count in strategy_types.items():
                st.write(f"• {strategy_type}: {count} 个标的")

        # 详细配置列表
        with st.expander("📄 详细配置信息", expanded=False):
            for symbol, name in selected_options:
                if self.session_state.get(f"{symbol}_has_custom_config", False):
                    strategy_type = self.session_state.get(f"strategy_type_{symbol}", "未设置")
                    has_rules = any([
                        self.session_state.get(f"open_rule_{symbol}", "").strip(),
                        self.session_state.get(f"close_rule_{symbol}", "").strip(),
                        self.session_state.get(f"buy_rule_{symbol}", "").strip(),
                        self.session_state.get(f"sell_rule_{symbol}", "").strip()
                    ])
                    rules_status = "✅ 已配置规则" if has_rules else "⚠️ 未配置规则"
                    st.write(f"• **{symbol}** ({name}): {strategy_type} - {rules_status}")
                else:
                    st.write(f"• **{symbol}** ({name}): ⚠️ 未配置")

    def _get_asset_config_status(self, symbol: str) -> Dict[str, Any]:
        """
        获取标的配置状态

        Args:
            symbol: 标的代码

        Returns:
            配置状态字典
        """
        return {
            'has_custom': self.session_state.get(f"{symbol}_has_custom_config", False),
            'strategy_type': self.session_state.get(f"strategy_type_{symbol}", ""),
            'has_rules': any([
                self.session_state.get(f"open_rule_{symbol}", "").strip(),
                self.session_state.get(f"close_rule_{symbol}", "").strip(),
                self.session_state.get(f"buy_rule_{symbol}", "").strip(),
                self.session_state.get(f"sell_rule_{symbol}", "").strip()
            ])
        }

    def _get_global_default_config(self) -> Dict[str, str]:
        """获取全局默认配置"""
        return {
            'strategy_type': self.session_state.get('global_default_strategy_type', '月定投'),
            'open_rule': self.session_state.get('global_open_rule', ''),
            'close_rule': self.session_state.get('global_close_rule', ''),
            'buy_rule': self.session_state.get('global_buy_rule', ''),
            'sell_rule': self.session_state.get('global_sell_rule', '')
        }

    def _apply_global_settings_to_all(self, selected_options: List[Tuple[str, str]],
                                    global_strategy_type: str, rule_group_manager):
        """
        应用全局设置到所有标的

        Args:
            selected_options: 选择的标的列表
            global_strategy_type: 全局策略类型
            rule_group_manager: 规则组管理器
        """
        for symbol, _ in selected_options:
            # 设置策略类型
            self.session_state[f"strategy_type_{symbol}"] = global_strategy_type

            # 如果是自定义规则，复制全局规则
            if global_strategy_type == "自定义规则":
                self.session_state[f"open_rule_{symbol}"] = self.session_state.get("global_open_rule", "")
                self.session_state[f"close_rule_{symbol}"] = self.session_state.get("global_close_rule", "")
                self.session_state[f"buy_rule_{symbol}"] = self.session_state.get("global_buy_rule", "")
                self.session_state[f"sell_rule_{symbol}"] = self.session_state.get("global_sell_rule", "")

            # 标记为自定义配置
            self.session_state[f"{symbol}_has_custom_config"] = True

    def _copy_config_to_targets(self, source_symbol: str, target_symbols: List[str]):
        """
        复制配置到目标标的

        Args:
            source_symbol: 源标的代码
            target_symbols: 目标标的代码列表
        """
        # 复制策略类型
        source_strategy_type = self.session_state.get(f"strategy_type_{source_symbol}", "")

        # 复制规则
        rules = {
            'open_rule': self.session_state.get(f"open_rule_{source_symbol}", ""),
            'close_rule': self.session_state.get(f"close_rule_{source_symbol}", ""),
            'buy_rule': self.session_state.get(f"buy_rule_{source_symbol}", ""),
            'sell_rule': self.session_state.get(f"sell_rule_{source_symbol}", "")
        }

        for target_symbol in target_symbols:
            self.session_state[f"strategy_type_{target_symbol}"] = source_strategy_type
            self.session_state[f"open_rule_{target_symbol}"] = rules['open_rule']
            self.session_state[f"close_rule_{target_symbol}"] = rules['close_rule']
            self.session_state[f"buy_rule_{target_symbol}"] = rules['buy_rule']
            self.session_state[f"sell_rule_{target_symbol}"] = rules['sell_rule']
            self.session_state[f"{target_symbol}_has_custom_config"] = True

    def _batch_apply_strategy_type(self, selected_options: List[Tuple[str, str]], strategy_type: str):
        """
        批量应用策略类型

        Args:
            selected_options: 选择的标的列表
            strategy_type: 策略类型
        """
        for symbol, _ in selected_options:
            self.session_state[f"strategy_type_{symbol}"] = strategy_type
            self.session_state[f"{symbol}_has_custom_config"] = True

    def _reset_all_individual_configs(self, selected_options: List[Tuple[str, str]]):
        """
        重置所有个别配置

        Args:
            selected_options: 选择的标的列表
        """
        for symbol, _ in selected_options:
            self.session_state[f"{symbol}_has_custom_config"] = False

    def _copy_global_rules_to_asset(self, symbol: str):
        """
        复制全局规则到标的

        Args:
            symbol: 标的代码
        """
        global_config = self._get_global_default_config()
        self.session_state[f"open_rule_{symbol}"] = global_config['open_rule']
        self.session_state[f"close_rule_{symbol}"] = global_config['close_rule']
        self.session_state[f"buy_rule_{symbol}"] = global_config['buy_rule']
        self.session_state[f"sell_rule_{symbol}"] = global_config['sell_rule']

    def _reset_asset_to_global(self, symbol: str):
        """
        重置标的为全局默认

        Args:
            symbol: 标的代码
        """
        self.session_state[f"{symbol}_has_custom_config"] = False

    def _apply_global_rule_group(self, group_name: str, rule_group_manager):
        """
        应用全局规则组

        Args:
            group_name: 规则组名称
            rule_group_manager: 规则组管理器
        """
        group = rule_group_manager.get_rule_group(group_name)
        if group:
            # 获取规则值
            global_open_rule = group.get('open_rule', '')
            global_close_rule = group.get('close_rule', '')
            global_buy_rule = group.get('buy_rule', '')
            global_sell_rule = group.get('sell_rule', '')

            # 更新原始session state key
            self.session_state["global_open_rule"] = global_open_rule
            self.session_state["global_close_rule"] = global_close_rule
            self.session_state["global_buy_rule"] = global_buy_rule
            self.session_state["global_sell_rule"] = global_sell_rule

            # 更新widget的session state key
            self.session_state["global_open_rule_widget"] = global_open_rule
            self.session_state["global_close_rule_widget"] = global_close_rule
            self.session_state["global_buy_rule_widget"] = global_buy_rule
            self.session_state["global_sell_rule_widget"] = global_sell_rule

            # 强制触发重新运行以更新UI
            import streamlit as st
            st.rerun()

    def _apply_rule_group_to_asset(self, symbol: str, group_name: str, rule_group_manager):
        """
        应用规则组到标的

        Args:
            symbol: 标的代码
            group_name: 规则组名称
            rule_group_manager: 规则组管理器
        """
        group = rule_group_manager.get_rule_group(group_name)
        if group:
            # 获取规则值
            open_rule = group.get('open_rule', '')
            close_rule = group.get('close_rule', '')
            buy_rule = group.get('buy_rule', '')
            sell_rule = group.get('sell_rule', '')

            # 更新原始session state key
            self.session_state[f"open_rule_{symbol}"] = open_rule
            self.session_state[f"close_rule_{symbol}"] = close_rule
            self.session_state[f"buy_rule_{symbol}"] = buy_rule
            self.session_state[f"sell_rule_{symbol}"] = sell_rule

            # 更新widget的session state key
            self.session_state[f"open_rule_{symbol}_widget"] = open_rule
            self.session_state[f"close_rule_{symbol}_widget"] = close_rule
            self.session_state[f"buy_rule_{symbol}_widget"] = buy_rule
            self.session_state[f"sell_rule_{symbol}_widget"] = sell_rule

            # 强制触发重新运行以更新UI
            import streamlit as st
            st.rerun()

    def _clear_asset_rules(self, symbol: str):
        """
        清空标的所有规则

        Args:
            symbol: 标的代码
        """
        self.session_state[f"open_rule_{symbol}"] = ''
        self.session_state[f"close_rule_{symbol}"] = ''
        self.session_state[f"buy_rule_{symbol}"] = ''
        self.session_state[f"sell_rule_{symbol}"] = ''

    def _clear_global_rules(self):
        """清空全局规则"""
        self.session_state["global_open_rule"] = ''
        self.session_state["global_close_rule"] = ''
        self.session_state["global_buy_rule"] = ''
        self.session_state["global_sell_rule"] = ''

    def _fill_global_example_rules(self):
        """填充示例全局规则"""
        self.session_state["global_open_rule"] = "close > ma20 and volume > ma(volume, 20)"
        self.session_state["global_close_rule"] = "close < ma20 or rsi > 70"
        self.session_state["global_buy_rule"] = "rsi < 30 and close > ma60"
        self.session_state["global_sell_rule"] = "rsi > 80 or macd < macd_signal"

    def _show_rules_help_modal(self):
        """显示规则编写帮助弹窗"""
        # 使用Streamlit的dialog功能（如果支持）或者使用expander作为弹窗
        with st.expander("📖 规则编写帮助", expanded=True):
            st.markdown("### 📝 规则编写指南")

            tab1, tab2, tab3 = st.tabs(["📊 常用指标", "⚡ 操作符", "💡 示例规则"])

            with tab1:
                st.markdown("#### **常用指标参考**")
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("**价格数据**")
                    st.code("close   # 收盘价")
                    st.code("open    # 开盘价")
                    st.code("high    # 最高价")
                    st.code("low     # 最低价")
                    st.code("volume  # 成交量")

                with col2:
                    st.markdown("**技术指标**")
                    st.code("ma20, ma60        # 移动平均线")
                    st.code("ema20, ema60      # 指数移动平均线")
                    st.code("rsi              # RSI相对强弱指标")
                    st.code("macd, macd_signal # MACD指标")
                    st.code("bb_upper, bb_lower # 布林带上下轨")

            with tab2:
                st.markdown("#### **常用操作符**")
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("**比较操作符**")
                    st.code(">   # 大于")
                    st.code("<   # 小于")
                    st.code(">=  # 大于等于")
                    st.code("<=  # 小于等于")
                    st.code("==  # 等于")
                    st.code("!=  # 不等于")

                with col2:
                    st.markdown("**逻辑操作符**")
                    st.code("and  # 逻辑与")
                    st.code("or   # 逻辑或")
                    st.code("not  # 逻辑非")
                    st.markdown("**算术操作符**")
                    st.code("+ - * /  # 四则运算")

            with tab3:
                st.markdown("#### **示例规则**")
                st.markdown("**开仓条件示例**:")
                examples_open = [
                    "close > ma20 and volume > ma(volume, 20)",
                    "rsi < 30 and close > ma60",
                    "macd > macd_signal and close > bb_lower"
                ]
                for example in examples_open:
                    st.code(example)

                st.markdown("**清仓条件示例**:")
                examples_close = [
                    "close < ma20 or rsi > 70",
                    "rsi > 80 or macd < macd_signal",
                    "close < bb_lower"
                ]
                for example in examples_close:
                    st.code(example)

                st.markdown("**💡 编写技巧**:")
                st.write("• 使用括号明确运算优先级")
                st.write("• 结合多个指标提高准确性")
                st.write("• 考虑成交量确认价格突破")
                st.write("• 设置止损条件控制风险")

    def get_strategy_summary(self) -> dict:
        """
        获取策略配置摘要

        Returns:
            策略配置摘要字典
        """
        global_config = self._get_global_default_config()
        individual_configs = {}

        # 收集个别配置
        symbols = [k.replace('_has_custom_config', '') for k in self.session_state.keys()
                  if k.endswith('_has_custom_config') and self.session_state[k]]

        for symbol in symbols:
            individual_configs[symbol] = {
                'strategy_type': self.session_state.get(f'strategy_type_{symbol}', ''),
                'use_custom': True,
                'rules': {
                    'open_rule': self.session_state.get(f'open_rule_{symbol}', ''),
                    'close_rule': self.session_state.get(f'close_rule_{symbol}', ''),
                    'buy_rule': self.session_state.get(f'buy_rule_{symbol}', ''),
                    'sell_rule': self.session_state.get(f'sell_rule_{symbol}', '')
                }
            }

        return {
            'mode': 'multi',
            'global_strategy_type': global_config['strategy_type'],
            'global_rules': global_config,
            'individual_configs': individual_configs
        }

    def sync_config_with_backtest_config(self, backtest_config):
        """
        同步UI配置到回测配置对象

        Args:
            backtest_config: 回测配置对象
        """
        # 设置全局默认策略
        global_config = self._get_global_default_config()
        backtest_config.default_strategy_type = global_config['strategy_type']

        if global_config['strategy_type'] == "自定义规则":
            backtest_config.default_custom_rules = {
                'open_rule': global_config['open_rule'],
                'close_rule': global_config['close_rule'],
                'buy_rule': global_config['buy_rule'],
                'sell_rule': global_config['sell_rule']
            }

        # 设置个别标的策略映射
        strategy_mapping = {}
        symbols = [k.replace('_has_custom_config', '') for k in self.session_state.keys()
                  if k.endswith('_has_custom_config') and self.session_state[k]]

        for symbol in symbols:
            strategy_mapping[symbol] = {
                'type': self.session_state.get(f'strategy_type_{symbol}', ''),
                'use_custom': True
            }

            if self.session_state.get(f'strategy_type_{symbol}') == "自定义规则":
                strategy_mapping[symbol]['rules'] = {
                    'open_rule': self.session_state.get(f'open_rule_{symbol}', ''),
                    'close_rule': self.session_state.get(f'close_rule_{symbol}', ''),
                    'buy_rule': self.session_state.get(f'buy_rule_{symbol}', ''),
                    'sell_rule': self.session_state.get(f'sell_rule_{symbol}', '')
                }

        backtest_config.strategy_mapping = strategy_mapping

    def validate_configuration(self) -> tuple[bool, str]:
        """
        验证多标配置的合法性

        Returns:
            (is_valid, error_message): 验证结果和错误信息
        """
        # 取消全局配置验证
        # # 检查全局配置
        # global_config = self._get_global_default_config()
        # if not global_config['strategy_type']:
        #     return False, "未设置全局默认策略类型"

        # 检查自定义规则的标的配置
        symbols = [k.replace('_has_custom_config', '') for k in self.session_state.keys()
                  if k.endswith('_has_custom_config') and self.session_state[k]]

        for symbol in symbols:
            strategy_type = self.session_state.get(f'strategy_type_{symbol}', '')
            if not strategy_type:
                return False, f"标的 {symbol} 未设置策略类型"

            # 如果不是自定义规则，则跳过规则验证
            if strategy_type != "自定义规则":
                continue

            # 检查是否有规则配置
            has_any_rule = any([
                self.session_state.get(f'open_rule_{symbol}', '').strip(),
                self.session_state.get(f'close_rule_{symbol}', '').strip(),
                self.session_state.get(f'buy_rule_{symbol}', '').strip(),
                self.session_state.get(f'sell_rule_{symbol}', '').strip()
            ])

            if not has_any_rule:
                return False, f"标的 {symbol} 的自定义策略模式下必须配置至少一个交易规则"

        return True, "配置验证通过"

    def _export_rules_to_json(self, symbol: str):
        """
        导出规则配置为JSON格式到剪贴板

        Args:
            symbol: 标的代码
        """
        import json
        from datetime import datetime

        # 获取当前规则配置
        rules_config = {
            "symbol": symbol,
            "rules": {
                "open_rule": self.session_state.get(f"open_rule_{symbol}", ""),
                "close_rule": self.session_state.get(f"close_rule_{symbol}", ""),
                "buy_rule": self.session_state.get(f"buy_rule_{symbol}", ""),
                "sell_rule": self.session_state.get(f"sell_rule_{symbol}", "")
            },
            "export_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "version": "1.0",
            "description": f"{symbol} 的交易规则配置"
        }

        # 转换为JSON字符串
        json_str = json.dumps(rules_config, ensure_ascii=False, indent=2)

        # 显示JSON内容供复制
        st.subheader(f"📤 导出 {symbol} 规则配置")
        st.write("请复制下面的JSON配置到剪贴板：")

        # 使用代码框显示JSON内容，方便复制
        st.code(json_str, language="json")

        # 复制按钮
        symbol_safe = symbol.replace('.', '_')
        json_safe = json_str.replace('`', '\\`').replace('${', '\\${')

        st.markdown(f"""
        <script>
        function copyToClipboard_{symbol_safe}() {{
            navigator.clipboard.writeText(`{json_safe}`).then(function() {{
                alert('配置已复制到剪贴板！');
            }}, function(err) {{
                console.error('复制失败: ', err);
            }});
        }}
        </script>
        <button onclick="copyToClipboard_{symbol_safe}()">📋 复制到剪贴板</button>
        """, unsafe_allow_html=True)

        st.success(f"✅ {symbol} 规则配置已生成，请复制上方JSON内容")

    def _import_rules_from_json(self, symbol: str):
        """
        从剪贴板导入规则配置

        Args:
            symbol: 标的代码
        """
        import json

        st.subheader(f"📥 导入 {symbol} 规则配置")
        st.write("请将JSON配置粘贴到下方文本框中：")

        # 文本输入框用于粘贴JSON
        json_input = st.text_area(
            "JSON配置内容",
            height=200,
            key=f"json_input_{symbol}",
            help="粘贴从剪贴板复制的JSON规则配置",
            placeholder='{"symbol": "AAPL", "rules": {...}, ...}'
        )

        # 导入按钮
        if st.button(f"🔄 导入配置", key=f"import_button_{symbol}"):
            if not json_input.strip():
                st.error(f"❌ 请粘贴JSON配置内容")
                return

            try:
                # 解析JSON内容
                rules_config = json.loads(json_input)

                # 验证配置格式
                if not self._validate_rules_config(rules_config):
                    st.error(f"❌ 配置文件格式错误，请检查JSON格式")
                    return

                # 应用规则配置
                rules = rules_config.get("rules", {})
                self.session_state[f"open_rule_{symbol}"] = rules.get("open_rule", "")
                self.session_state[f"close_rule_{symbol}"] = rules.get("close_rule", "")
                self.session_state[f"buy_rule_{symbol}"] = rules.get("buy_rule", "")
                self.session_state[f"sell_rule_{symbol}"] = rules.get("sell_rule", "")

                # 标记为自定义配置
                self.session_state[f"{symbol}_has_custom_config"] = True

                # 显示导入结果
                source_symbol = rules_config.get("symbol", "未知")
                st.success(f"✅ 成功导入规则配置 (来源: {source_symbol})")

                # 显示导入的规则摘要
                with st.expander(f"📄 导入的规则配置详情", expanded=True):
                    st.write(f"**来源标的**: {source_symbol}")
                    st.write(f"**版本**: {rules_config.get('version', '未知')}")
                    st.write(f"**导出时间**: {rules_config.get('export_time', '未知')}")
                    st.write(f"**描述**: {rules_config.get('description', '无')}")

                    st.write("**导入的规则**:")
                    rules = rules_config.get("rules", {})
                    for rule_type, rule_content in rules.items():
                        if rule_type == "open_rule":
                            rule_name = "开仓条件"
                        elif rule_type == "close_rule":
                            rule_name = "清仓条件"
                        elif rule_type == "buy_rule":
                            rule_name = "加仓条件"
                        elif rule_type == "sell_rule":
                            rule_name = "平仓条件"
                        else:
                            rule_name = rule_type

                        if rule_content.strip():
                            st.code(f"{rule_name}: {rule_content}")
                        else:
                            st.write(f"• {rule_name}: (空)")

            except json.JSONDecodeError as e:
                st.error(f"❌ JSON格式错误: {str(e)}")
            except Exception as e:
                st.error(f"❌ 导入配置失败: {str(e)}")

    def _validate_rules_config(self, config: dict) -> bool:
        """
        验证规则配置格式

        Args:
            config: 配置字典

        Returns:
            是否为有效配置
        """
        # 检查必需字段
        if not isinstance(config, dict):
            return False

        if "rules" not in config:
            return False

        rules = config["rules"]
        if not isinstance(rules, dict):
            return False

        # 检查规则字段
        required_fields = ["open_rule", "close_rule", "buy_rule", "sell_rule"]
        for field in required_fields:
            if field not in rules:
                return False

        return True