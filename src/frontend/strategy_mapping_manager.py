import streamlit as st
from typing import Dict, Any, List

class StrategyMappingManager:
    """策略映射管理类，负责多股票策略映射配置"""

    def __init__(self, session_state):
        self.session_state = session_state

    def initialize_strategy_mapping(self):
        """初始化策略映射"""
        if 'strategy_mapping' not in self.session_state:
            self.session_state.strategy_mapping = {}

    def get_strategy_mapping(self) -> Dict[str, Dict[str, Any]]:
        """获取策略映射配置"""
        return self.session_state.get('strategy_mapping', {})

    def set_strategy_for_symbol(self, symbol: str, strategy_config: Dict[str, Any]):
        """为指定股票设置策略配置"""
        self.session_state.strategy_mapping[symbol] = strategy_config

    def remove_strategy_for_symbol(self, symbol: str):
        """移除指定股票的策略配置"""
        if symbol in self.session_state.strategy_mapping:
            del self.session_state.strategy_mapping[symbol]

    def get_strategy_for_symbol(self, symbol: str) -> Dict[str, Any]:
        """获取指定股票的策略配置"""
        return self.session_state.strategy_mapping.get(symbol, {})

    def render_strategy_selection_ui(self, symbol: str, symbol_name: str,
                                   rule_group_options: List[str]) -> str:
        """渲染策略选择UI"""
        col1, col2 = st.columns([1, 1])

        with col1:
            # 策略选择选项
            strategy_options = ["使用默认策略", "月定投", "移动平均线交叉",
                              "MACD交叉", "RSI超买超卖", "自定义规则"] + rule_group_options

            strategy_choice = st.selectbox(
                f"选择策略类型",
                options=strategy_options,
                key=f"strategy_type_{symbol}"
            )

        with col2:
            # 显示当前策略状态
            if strategy_choice == "使用默认策略":
                st.info("使用默认策略配置")
            elif strategy_choice.startswith("规则组:"):
                group_name = strategy_choice.replace("规则组: ", "")
                st.success(f"使用规则组: {group_name}")
            else:
                st.success(f"使用自定义策略: {strategy_choice}")

        return strategy_choice

    def render_custom_rules_ui(self, symbol: str):
        """渲染自定义规则UI"""
        st.text_area(
            f"开仓条件 - {symbol}",
            value=st.session_state.get(f"open_rule_{symbol}", ""),
            height=60,
            key=f"open_rule_{symbol}",
            help="输入开仓条件表达式"
        )
        st.text_area(
            f"清仓条件 - {symbol}",
            value=st.session_state.get(f"close_rule_{symbol}", ""),
            height=60,
            key=f"close_rule_{symbol}",
            help="输入清仓条件表达式"
        )
        st.text_area(
            f"加仓条件 - {symbol}",
            value=st.session_state.get(f"buy_rule_{symbol}", ""),
            height=60,
            key=f"buy_rule_{symbol}",
            help="输入加仓条件表达式"
        )
        st.text_area(
            f"平仓条件 - {symbol}",
            value=st.session_state.get(f"sell_rule_{symbol}", ""),
            height=60,
            key=f"sell_rule_{symbol}",
            help="输入平仓条件表达式"
        )

    def update_strategy_mapping_from_ui(self, symbol: str, strategy_choice: str,
                                       rule_group_manager):
        """根据UI选择更新策略映射"""
        if strategy_choice != "使用默认策略":
            if strategy_choice.startswith("规则组:"):
                # 处理规则组选择
                group_name = strategy_choice.replace("规则组: ", "")
                group = rule_group_manager.get_rule_group(group_name)

                if group:
                    strategy_config = {
                        'type': "自定义规则",
                        'buy_rule': group.get('buy_rule', ''),
                        'sell_rule': group.get('sell_rule', ''),
                        'open_rule': group.get('open_rule', ''),
                        'close_rule': group.get('close_rule', '')
                    }
                    self.set_strategy_for_symbol(symbol, strategy_config)

                    # 同时更新session state中的规则值，以便在界面上显示
                    st.session_state[f"buy_rule_{symbol}"] = group.get('buy_rule', '')
                    st.session_state[f"sell_rule_{symbol}"] = group.get('sell_rule', '')
                    st.session_state[f"open_rule_{symbol}"] = group.get('open_rule', '')
                    st.session_state[f"close_rule_{symbol}"] = group.get('close_rule', '')
            else:
                # 处理普通策略选择
                strategy_config = {
                    'type': strategy_choice,
                    'buy_rule': st.session_state.get(f"buy_rule_{symbol}", ""),
                    'sell_rule': st.session_state.get(f"sell_rule_{symbol}", ""),
                    'open_rule': st.session_state.get(f"open_rule_{symbol}", ""),
                    'close_rule': st.session_state.get(f"close_rule_{symbol}", "")
                }
                self.set_strategy_for_symbol(symbol, strategy_config)
        else:
            # 使用默认策略，移除该股票的映射
            self.remove_strategy_for_symbol(symbol)

    def render_multi_symbol_strategy_ui(self, selected_options: List[tuple],
                                       rule_group_manager, config_manager):
        """渲染多股票策略配置UI"""
        if not selected_options or len(selected_options) <= 1:
            return

        self.initialize_strategy_mapping()
        rule_group_options = rule_group_manager.get_rule_options_for_display()

        st.write("**各股票策略配置**")

        for symbol_option in selected_options:
            symbol = symbol_option[0]
            symbol_name = symbol_option[1]

            # 为每个股票创建扩展器来配置策略
            with st.expander(f"{symbol} - {symbol_name}", expanded=False):
                # 策略选择
                strategy_choice = self.render_strategy_selection_ui(
                    symbol, symbol_name, rule_group_options
                )

                # 如果选择自定义规则，显示规则编辑器
                if strategy_choice == "自定义规则":
                    self.render_custom_rules_ui(symbol)

                # 更新策略映射
                self.update_strategy_mapping_from_ui(symbol, strategy_choice, rule_group_manager)

        # 更新配置对象中的策略映射
        config = config_manager.get_config()
        config.strategy_mapping = self.get_strategy_mapping()

    def get_default_strategy_config(self) -> Dict[str, Any]:
        """获取默认策略配置"""
        return {
            'type': st.session_state.get("default_strategy_type", "使用默认策略"),
            'buy_rule': st.session_state.get("default_buy_rule_editor", ""),
            'sell_rule': st.session_state.get("default_sell_rule_editor", ""),
            'open_rule': st.session_state.get("default_open_rule_editor", ""),
            'close_rule': st.session_state.get("default_close_rule_editor", "")
        }

    def update_config_default_strategy(self, config_manager):
        """更新配置中的默认策略"""
        config = config_manager.get_config()
        config.default_strategy = self.get_default_strategy_config()

    def validate_strategy_configs(self) -> bool:
        """验证所有策略配置的合法性"""
        # 这里可以添加更复杂的验证逻辑
        # 例如检查规则语法、策略参数范围等
        return True