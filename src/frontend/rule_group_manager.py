import streamlit as st
from src.core.strategy.rule_parser import RuleParser
from typing import Dict, Any

class RuleGroupManager:
    """规则组管理类，负责规则组的CRUD操作和语法验证"""

    def __init__(self, session_state):
        self.session_state = session_state

    def initialize_default_rule_groups(self):
        """初始化默认规则组"""
        if 'rule_groups' not in self.session_state:
            self.session_state.rule_groups = {
                '金叉死叉': {
                    'buy_rule': '(REF(SMA(close,5), 1) < REF(SMA(close,7), 1)) & (SMA(close,5) > SMA(close,7))',
                    'sell_rule': '(REF(SMA(close,5), 1) > REF(SMA(close,7), 1)) & (SMA(close,5) < SMA(close,7))'
                },
                '相对强度': {
                    'buy_rule': '(REF(RSI(close,5), 1) < 30) & (RSI(close,5) >= 30)',
                    'sell_rule': '(REF(RSI(close,5), 1) >= 60) & (RSI(close,5) < 60)'
                },
                'Martingale': {
                    'open_rule': '(close < REF(SMA(close,5), 1)) & (close > SMA(close,5))',
                    'close_rule': '(close - (COST/POSITION))/(COST/POSITION) * 100 >= 5',
                    'buy_rule': '(close - (COST/POSITION))/(COST/POSITION) * 100 <= -5',
                    'sell_rule': ''
                }
            }

        # 初始化默认规则编辑器状态
        if 'buy_rule_default' not in self.session_state:
            self.session_state.buy_rule_default = ''
        if 'sell_rule_default' not in self.session_state:
            self.session_state.sell_rule_default = ''
        if 'open_rule_default' not in self.session_state:
            self.session_state.open_rule_default = ''
        if 'close_rule_default' not in self.session_state:
            self.session_state.close_rule_default = ''

    def get_rule_groups(self) -> Dict[str, Dict[str, str]]:
        """获取所有规则组"""
        return self.session_state.get('rule_groups', {})

    def get_rule_group_names(self) -> list:
        """获取规则组名称列表"""
        return list(self.get_rule_groups().keys())

    def get_rule_group(self, group_name: str) -> Dict[str, str]:
        """获取指定规则组"""
        return self.get_rule_groups().get(group_name, {})

    def create_rule_group(self, group_name: str, rules: Dict[str, str]) -> bool:
        """创建新规则组"""
        if not group_name or not group_name.strip():
            st.error("规则组名称不能为空")
            return False

        if group_name in self.get_rule_groups():
            st.error(f"规则组 '{group_name}' 已存在")
            return False

        # 验证规则语法
        for rule_type, rule_expr in rules.items():
            if rule_expr and not self.validate_rule_syntax(rule_expr):
                return False

        self.session_state.rule_groups[group_name] = rules
        st.success(f"规则组 '{group_name}' 创建成功")
        return True

    def update_rule_group(self, group_name: str, rules: Dict[str, str]) -> bool:
        """更新规则组"""
        if group_name not in self.get_rule_groups():
            st.error(f"规则组 '{group_name}' 不存在")
            return False

        # 验证规则语法
        for rule_type, rule_expr in rules.items():
            if rule_expr and not self.validate_rule_syntax(rule_expr):
                return False

        self.session_state.rule_groups[group_name] = rules
        st.success(f"规则组 '{group_name}' 更新成功")
        return True

    def delete_rule_group(self, group_name: str) -> bool:
        """删除规则组"""
        if group_name not in self.get_rule_groups():
            st.error(f"规则组 '{group_name}' 不存在")
            return False

        del self.session_state.rule_groups[group_name]
        st.success(f"规则组 '{group_name}' 删除成功")
        return True

    def validate_rule_syntax(self, rule_expr: str) -> bool:
        """验证规则语法"""
        if not rule_expr:
            return True

        valid, msg = RuleParser.validate_syntax(rule_expr)
        if not valid:
            st.error(f"规则语法错误: {msg}")
        return valid

    def render_rule_group_selector(self, key_suffix: str = "") -> str:
        """渲染规则组选择器"""
        rule_groups = self.get_rule_groups()
        if not rule_groups:
            st.info("暂无规则组，请先创建规则组")
            return ""

        selected_group = st.selectbox(
            "选择规则组",
            options=list(rule_groups.keys()),
            key=f"rule_group_select_{key_suffix}"
        )
        return selected_group

    def load_rule_group_to_session(self, group_name: str, prefix: str = "default"):
        """加载规则组到会话状态"""
        group = self.get_rule_group(group_name)
        if not group:
            st.error(f"规则组 '{group_name}' 不存在")
            return False

        # 设置加载状态和规则值
        self.session_state[f"{prefix}_rule_group_loaded"] = True

        # 设置当前选中的规则组名称 - 这是关键！
        self.session_state['selected_rule_group'] = group_name
        self.session_state[f'selected_rule_group_{prefix}'] = group_name

        # 更新UI控件的值和默认值
        self.session_state[f"open_rule_{prefix}"] = group.get('open_rule', '')
        self.session_state[f"close_rule_{prefix}"] = group.get('close_rule', '')
        self.session_state[f"buy_rule_{prefix}"] = group.get('buy_rule', '')
        self.session_state[f"sell_rule_{prefix}"] = group.get('sell_rule', '')

        # 设置默认值供UI使用
        self.session_state['open_rule_default'] = group.get('open_rule', '')
        self.session_state['close_rule_default'] = group.get('close_rule', '')
        self.session_state['buy_rule_default'] = group.get('buy_rule', '')
        self.session_state['sell_rule_default'] = group.get('sell_rule', '')

        # 保存规则组配置到专门的配置属性中
        self.session_state['current_rule_group_config'] = {
            'group_name': group_name,
            'rules': group
        }

        st.success(f"已加载规则组: {group_name}")
        return True

    def render_rule_editor_ui(self, rule_type: str, default_value: str = "",
                             key_suffix: str = "", height: int = 60) -> str:
        """渲染规则编辑器UI"""
        rule_descriptions = {
            'open_rule': "开仓条件表达式",
            'close_rule': "清仓条件表达式",
            'buy_rule': "加仓条件表达式",
            'sell_rule': "平仓条件表达式"
        }

        display_name = rule_descriptions.get(rule_type, rule_type)

        return st.text_area(
            display_name,
            height=height,
            key=f"{rule_type}_{key_suffix}",
            help=f"输入{display_name}"
        )

    def render_rule_validation_ui(self, rule_key: str, display_name: str):
        """渲染规则验证UI"""
        if rule_key in st.session_state and st.session_state[rule_key]:
            rule_expr = st.session_state[rule_key]
            valid, msg = RuleParser.validate_syntax(rule_expr)

            if valid:
                st.success(f"✓ {display_name}语法正确")
                st.code(f"{display_name}: {rule_expr}")
            else:
                st.error(f"{display_name}错误: {msg}")

    def render_rule_group_management_ui(self, prefix: str = "default"):
        """渲染规则组管理UI"""
        st.subheader("规则组管理")

        # 规则组选择器
        selected_group = self.render_rule_group_selector(prefix)

        # 加载规则组按钮
        if st.button("加载规则组到当前策略", key=f"load_rule_group_{prefix}"):
            self.load_rule_group_to_session(selected_group, prefix)
            st.rerun()

        # 保存为规则组
        if st.button("保存当前为规则组", key=f"save_rule_group_{prefix}"):
            group_name = st.text_input("输入规则组名称", key=f"new_rule_group_name_{prefix}")
            if group_name and group_name.strip():
                rules = {
                    'open_rule': st.session_state.get(f'open_rule_{prefix}', ''),
                    'close_rule': st.session_state.get(f'close_rule_{prefix}', ''),
                    'buy_rule': st.session_state.get(f'buy_rule_{prefix}', ''),
                    'sell_rule': st.session_state.get(f'sell_rule_{prefix}', '')
                }
                self.create_rule_group(group_name, rules)
                st.rerun()

    def get_rule_options_for_display(self) -> list:
        """获取用于显示的规则组选项"""
        return [f"规则组: {name}" for name in self.get_rule_group_names()]