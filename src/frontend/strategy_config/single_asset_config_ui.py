"""
单标策略配置UI组件
处理单个标的的策略配置界面
"""
import streamlit as st
from typing import Tuple
from .rule_validator import RuleValidator


class SingleAssetConfigUI:
    """单标策略配置UI组件"""

    def __init__(self, session_state):
        self.session_state = session_state
        self.rule_validator = RuleValidator()

    def render_configuration(self, selected_option: Tuple[str, str],
                           rule_group_manager, config_manager):
        """
        渲染单标策略配置界面

        Args:
            selected_option: 选择的标的 (symbol, name)
            rule_group_manager: 规则组管理器
            config_manager: 配置管理器
        """
        symbol, name = selected_option

        # 策略类型选择
        self._render_strategy_type_selection(symbol)

        # 自定义规则配置（如果选择自定义规则）
        self._render_custom_rules(symbol, rule_group_manager)

        # 策略配置摘要
        self._render_configuration_summary(symbol)

    def _render_strategy_type_selection(self, symbol: str):
        """
        渲染策略类型选择界面

        Args:
            symbol: 标的代码
        """
        st.subheader("📊 策略类型选择")

        # 获取动态 key 后缀（用于在加载配置后强制刷新 widget）
        key_suffix = self.session_state.get('_strategy_key_suffix', '')

        # 获取当前策略类型（优先从 session_state 读取加载的值）
        current_strategy_type = self.session_state.get(f'strategy_type_{symbol}', '月定投')
        from src.support.log.logger import logger
        logger.info(f"[策略类型UI] symbol={symbol}, key_suffix={key_suffix}, current_strategy_type={current_strategy_type}")

        # 计算索引
        strategy_options = ["月定投", "移动平均线交叉", "MACD交叉", "RSI超买超卖", "自定义规则"]
        try:
            index = strategy_options.index(current_strategy_type)
        except ValueError:
            index = 0
            current_strategy_type = strategy_options[0]

        # 策略类型选项
        strategy_type = st.selectbox(
            "选择策略类型",
            index=index,
            options=strategy_options,
            key=f"single_strategy_type_{symbol}_{key_suffix}",
            help="选择适用于该标的的策略类型"
        )

        # 更新session state
        self.session_state[f"strategy_type_{symbol}"] = strategy_type
        logger.info(f"[策略类型UI] 用户选择: strategy_type={strategy_type}")

        # 显示策略说明
        self._render_strategy_description(strategy_type)

    def _render_strategy_description(self, strategy_type: str):
        """
        渲染策略类型说明

        Args:
            strategy_type: 策略类型
        """
        descriptions = {
            "月定投": "每月固定时间进行定额投资，适合长期稳健投资",
            "移动平均线交叉": "基于移动平均线的金叉死叉信号进行买卖操作",
            "MACD交叉": "基于MACD指标的金叉死叉信号进行买卖操作",
            "RSI超买超卖": "基于RSI指标的超买超卖信号进行买卖操作",
            "自定义规则": "根据自定义的技术指标条件进行买卖操作"
        }

        if strategy_type in descriptions:
            st.info(f"💡 **策略说明**: {descriptions[strategy_type]}")

    def _render_custom_rules(self, symbol: str, rule_group_manager):
        """
        渲染自定义规则配置界面

        Args:
            symbol: 标的代码
            rule_group_manager: 规则组管理器
        """
        strategy_type = self.session_state.get(f"strategy_type_{symbol}", "")

        if strategy_type == "自定义规则":
            st.subheader("⚙️ 自定义交易规则")

            # 预定义规则组加载区域
            self._render_rule_group_loader(symbol, rule_group_manager)

            st.divider()  # 分割线

            # 手动配置规则区域
            st.write("**手动配置交易规则**")
            st.info("💡 您可以直接在下方编辑规则，或者先加载预定义规则组后进行修改")

            # 快速操作按钮
            col1, col2, col3 = st.columns([1, 1, 1.2])
            with col1:
                if st.button(f"📋 填充示例规则", key=f"fill_example_{symbol}"):
                    self._fill_example_rules(symbol)
                    st.success(f"✅ 已填充示例规则")

            with col2:
                if st.button(f"🧹 清空所有规则", key=f"clear_rules_{symbol}"):
                    self._clear_asset_rules(symbol)
                    st.success(f"✅ 已清空所有规则")

            with col3:
                if st.button(f"📖 规则编写帮助", key=f"help_rules_{symbol}"):
                    self._show_rules_help_modal()

            # 规则编辑器
            rule_col1, rule_col2 = st.columns(2)

            # 确保widget session state存在，如果不存在则从存储session state初始化
            if f"ta_open_rule_{symbol}" not in self.session_state:
                self.session_state[f"ta_open_rule_{symbol}"] = self.session_state.get(f"open_rule_{symbol}", "")
            if f"ta_close_rule_{symbol}" not in self.session_state:
                self.session_state[f"ta_close_rule_{symbol}"] = self.session_state.get(f"close_rule_{symbol}", "")
            if f"ta_buy_rule_{symbol}" not in self.session_state:
                self.session_state[f"ta_buy_rule_{symbol}"] = self.session_state.get(f"buy_rule_{symbol}", "")
            if f"ta_sell_rule_{symbol}" not in self.session_state:
                self.session_state[f"ta_sell_rule_{symbol}"] = self.session_state.get(f"sell_rule_{symbol}", "")

            with rule_col1:
                # 开仓条件输入框
                st.text_area(
                    "开仓条件",
                    height=80,
                    key=f"ta_open_rule_{symbol}",
                    help="输入开仓条件表达式，例如: close > ma20"
                )

                # 开仓条件验证结果
                self._render_rule_validation(f"ta_open_rule_{symbol}", "开仓条件", symbol)

                # 清仓条件输入框
                st.text_area(
                    "清仓条件",
                    height=80,
                    key=f"ta_close_rule_{symbol}",
                    help="输入清仓条件表达式，例如: close < ma20"
                )

                # 清仓条件验证结果
                self._render_rule_validation(f"ta_close_rule_{symbol}", "清仓条件", symbol)

            with rule_col2:
                # 加仓条件输入框
                st.text_area(
                    "加仓条件",
                    height=80,
                    key=f"ta_buy_rule_{symbol}",
                    help="输入加仓条件表达式，例如: rsi < 30"
                )

                # 加仓条件验证结果
                self._render_rule_validation(f"ta_buy_rule_{symbol}", "加仓条件", symbol)

                # 平仓条件输入框
                st.text_area(
                    "平仓条件",
                    height=80,
                    key=f"ta_sell_rule_{symbol}",
                    help="输入平仓条件表达式，例如: rsi > 70"
                )

                # 平仓条件验证结果
                self._render_rule_validation(f"ta_sell_rule_{symbol}", "平仓条件", symbol)

    def _render_rule_group_loader(self, symbol: str, rule_group_manager):
        """
        渲染规则组加载区域

        Args:
            symbol: 标的代码
            rule_group_manager: 规则组管理器
        """
        # 获取动态 key 后缀（用于在加载配置后强制刷新 widget）
        key_suffix = self.session_state.get('_strategy_key_suffix', '')

        # 获取可用的规则组
        rule_groups = rule_group_manager.get_rule_options_for_display()

        if rule_groups:
            st.write("**📦 加载预定义规则组**")

            # 清理规则组名称，移除前缀
            clean_rule_groups = [group.replace("规则组: ", "").strip() for group in rule_groups]

            # 使用columns布局，左侧选择框，右侧按钮
            col1, col2 = st.columns([3, 1])

            with col1:
                selected_group = st.selectbox(
                    "选择预定义规则组",
                    options=["请选择规则组"] + clean_rule_groups,
                    key=f"selected_rule_group_{symbol}_{key_suffix}",
                    help="选择要加载的预定义规则组"
                )

            with col2:
                # 将按钮垂直居中对齐
                st.markdown("<br>", unsafe_allow_html=True)  # 添加一些间距
                load_button_disabled = selected_group == "请选择规则组"
                if st.button(
                    f"🔄 加载规则组",
                    key=f"load_group_{symbol}_{key_suffix}",
                    disabled=load_button_disabled,
                    help="加载选择的规则组到下方编辑器中"
                ):
                    if selected_group != "请选择规则组":
                        self._apply_rule_group_settings(symbol, selected_group, rule_group_manager)
                        st.success(f"✅ 已加载规则组 '{selected_group}' 到编辑器中")
                        # st.rerun() 现在在 _apply_rule_group_settings 中调用

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

    def _apply_rule_group_settings(self, symbol: str, group_name: str, rule_group_manager):
        """
        应用规则组设置

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

            # 更新存储session state key（用于其他逻辑）
            self.session_state[f"open_rule_{symbol}"] = open_rule
            self.session_state[f"close_rule_{symbol}"] = close_rule
            self.session_state[f"buy_rule_{symbol}"] = buy_rule
            self.session_state[f"sell_rule_{symbol}"] = sell_rule

            # 更新widget session state key（用于显示）
            self.session_state[f"ta_open_rule_{symbol}"] = open_rule
            self.session_state[f"ta_close_rule_{symbol}"] = close_rule
            self.session_state[f"ta_buy_rule_{symbol}"] = buy_rule
            self.session_state[f"ta_sell_rule_{symbol}"] = sell_rule

            # 强制触发重新运行以更新UI
            import streamlit as st
            st.rerun()

    def _clear_asset_rules(self, symbol: str):
        """
        清空标的所有规则

        Args:
            symbol: 标的代码
        """
        # 清空存储session state key
        self.session_state[f"open_rule_{symbol}"] = ''
        self.session_state[f"close_rule_{symbol}"] = ''
        self.session_state[f"buy_rule_{symbol}"] = ''
        self.session_state[f"sell_rule_{symbol}"] = ''

        # 清空widget session state key
        self.session_state[f"ta_open_rule_{symbol}"] = ''
        self.session_state[f"ta_close_rule_{symbol}"] = ''
        self.session_state[f"ta_buy_rule_{symbol}"] = ''
        self.session_state[f"ta_sell_rule_{symbol}"] = ''

    def _fill_example_rules(self, symbol: str):
        """
        填充示例规则

        Args:
            symbol: 标的代码
        """
        # 定义示例规则
        open_rule = "close > ma20 and volume > ma(volume, 20)"
        close_rule = "close < ma20 or rsi > 70"
        buy_rule = "rsi < 30 and close > ma60"
        sell_rule = "rsi > 80 or macd < macd_signal"

        # 更新存储session state key
        self.session_state[f"open_rule_{symbol}"] = open_rule
        self.session_state[f"close_rule_{symbol}"] = close_rule
        self.session_state[f"buy_rule_{symbol}"] = buy_rule
        self.session_state[f"sell_rule_{symbol}"] = sell_rule

        # 更新widget session state key
        self.session_state[f"ta_open_rule_{symbol}"] = open_rule
        self.session_state[f"ta_close_rule_{symbol}"] = close_rule
        self.session_state[f"ta_buy_rule_{symbol}"] = buy_rule
        self.session_state[f"ta_sell_rule_{symbol}"] = sell_rule

    def _show_rules_help_modal(self):
        """显示规则编写帮助弹窗"""
        # 使用Streamlit的expander作为帮助弹窗
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

    def _render_configuration_summary(self, symbol: str):
        """
        渲染配置摘要

        Args:
            symbol: 标的代码
        """
        st.subheader("📋 配置摘要")

        strategy_type = self.session_state.get(f"strategy_type_{symbol}", "未设置")
        st.info(f"**策略类型**: {strategy_type}")

        if strategy_type == "自定义规则":
            rules = {
                "开仓条件": self.session_state.get(f"open_rule_{symbol}", ""),
                "清仓条件": self.session_state.get(f"close_rule_{symbol}", ""),
                "加仓条件": self.session_state.get(f"buy_rule_{symbol}", ""),
                "平仓条件": self.session_state.get(f"sell_rule_{symbol}", "")
            }

            configured_rules = [k for k, v in rules.items() if v.strip()]
            if configured_rules:
                st.info(f"**已配置规则**: {', '.join(configured_rules)}")
            else:
                st.warning("⚠️ 尚未配置任何交易规则")

    def get_strategy_summary(self) -> dict:
        """
        获取策略配置摘要

        Returns:
            策略配置摘要字典
        """
        # 获取第一个标的的信息（单标模式）
        symbols = [k.replace('strategy_type_', '') for k in self.session_state.keys()
                  if k.startswith('strategy_type_')]

        if not symbols:
            return {'mode': 'empty'}

        symbol = symbols[0]

        return {
            'mode': 'single',
            'symbol': symbol,
            'strategy_type': self.session_state.get(f'strategy_type_{symbol}', ''),
            'custom_rules': {
                'open_rule': self.session_state.get(f'open_rule_{symbol}', ''),
                'close_rule': self.session_state.get(f'close_rule_{symbol}', ''),
                'buy_rule': self.session_state.get(f'buy_rule_{symbol}', ''),
                'sell_rule': self.session_state.get(f'sell_rule_{symbol}', '')
            }
        }

    def sync_config_with_backtest_config(self, backtest_config):
        """
        同步UI配置到回测配置对象

        Args:
            backtest_config: 回测配置对象
        """
        from src.support.log.logger import logger

        # 从 backtest_config 获取当前选中的标的（单标模式）
        # 这样可以避免使用旧标的的策略类型
        symbol = backtest_config.target_symbol

        if not symbol:
            logger.warning("[同步配置] backtest_config.target_symbol 为空，无法同步策略类型")
            return

        key_suffix = self.session_state.get('_strategy_key_suffix', '')

        # 优先从实际的widget key读取策略类型
        widget_key = f"single_strategy_type_{symbol}_{key_suffix}"
        strategy_type = self.session_state.get(widget_key)

        # 如果widget key没有值，从手动设置的session_state读取
        if not strategy_type:
            strategy_type = self.session_state.get(f'strategy_type_{symbol}', '月定投')
            logger.info(f"[同步配置] widget_key={widget_key} 无值，使用 strategy_type_{symbol}={strategy_type}")
        else:
            logger.info(f"[同步配置] 从 widget_key={widget_key} 读取到 strategy_type={strategy_type}")

        backtest_config.strategy_type = strategy_type

        # 如果是自定义规则，设置规则配置
        if backtest_config.strategy_type == "自定义规则":
            backtest_config.custom_rules = {
                'open_rule': self.session_state.get(f'open_rule_{symbol}', ''),
                'close_rule': self.session_state.get(f'close_rule_{symbol}', ''),
                'buy_rule': self.session_state.get(f'buy_rule_{symbol}', ''),
                'sell_rule': self.session_state.get(f'sell_rule_{symbol}', '')
            }

    def validate_configuration(self) -> tuple[bool, str]:
        """
        验证单标配置的合法性

        Returns:
            (is_valid, error_message): 验证结果和错误信息
        """
        # 获取第一个标的的信息（单标模式）
        symbols = [k.replace('strategy_type_', '') for k in self.session_state.keys()
                  if k.startswith('strategy_type_')]

        if not symbols:
            return False, "未找到标的配置"

        symbol = symbols[0]
        strategy_type = self.session_state.get(f'strategy_type_{symbol}', '')

        if not strategy_type:
            return False, "未选择策略类型"

        if strategy_type == "自定义规则":
            # 检查是否配置了必要的规则
            has_any_rule = any([
                self.session_state.get(f'open_rule_{symbol}', '').strip(),
                self.session_state.get(f'close_rule_{symbol}', '').strip(),
                self.session_state.get(f'buy_rule_{symbol}', '').strip(),
                self.session_state.get(f'sell_rule_{symbol}', '').strip()
            ])

            if not has_any_rule:
                return False, "自定义策略模式下必须配置至少一个交易规则"

        return True, "配置验证通过"

    def _render_rule_validation(self, rule_key: str, rule_name: str, symbol: str):
        """
        渲染规则验证结果

        Args:
            rule_key: 规则在session state中的键
            rule_name: 规则显示名称
            symbol: 标的代码
        """
        rule_expr = self.session_state.get(rule_key, "").strip()

        if not rule_expr:
            # 空规则显示灰色提示
            st.markdown(f"<small style='color: #888888;'>📝 {rule_name}: 未输入规则</small>", unsafe_allow_html=True)
            return

        # 验证规则
        is_valid, error_message = self.rule_validator.validate_rule_syntax(rule_expr)

        if is_valid:
            # 验证成功显示绿色提示
            st.markdown(f"<small style='color: #00AA00;'>✅ {rule_name}: 语法正确</small>", unsafe_allow_html=True)
        else:
            # 验证失败显示红色错误
            st.markdown(f"<small style='color: #FF0000;'>❌ {rule_name}: {error_message}</small>", unsafe_allow_html=True)