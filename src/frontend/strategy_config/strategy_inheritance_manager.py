"""
策略继承管理器
处理多标环境下的策略继承和优先级逻辑
"""
from typing import Dict, Any, List, Optional
import streamlit as st


class StrategyInheritanceManager:
    """策略继承管理器"""

    def __init__(self, session_state):
        self.session_state = session_state

    def get_effective_strategies(self, backtest_config) -> Dict[str, Dict[str, Any]]:
        """
        获取所有标的的有效策略配置

        Args:
            backtest_config: 回测配置对象

        Returns:
            每个标的的有效策略配置字典
        """
        effective_strategies = {}
        target_symbols = backtest_config.get_symbols()

        # 获取全局默认配置
        global_default = self._get_global_default_config(backtest_config)

        for symbol in target_symbols:
            # 获取标的的个别配置
            individual_config = self._get_individual_config(symbol, backtest_config)

            # 应用继承逻辑，获取有效配置
            effective_config = self._apply_inheritance(symbol, global_default, individual_config)
            effective_strategies[symbol] = effective_config

        return effective_strategies

    def _get_global_default_config(self, backtest_config) -> Dict[str, Any]:
        """
        获取全局默认配置

        Args:
            backtest_config: 回测配置对象

        Returns:
            全局默认配置字典
        """
        # 优先使用UI中的全局配置
        if hasattr(backtest_config, 'default_strategy_type'):
            strategy_type = backtest_config.default_strategy_type
        else:
            strategy_type = self.session_state.get('global_default_strategy_type', '月定投')

        global_config = {
            'strategy_type': strategy_type,
            'source': 'global_default'
        }

        # 如果是自定义规则，获取规则配置
        if strategy_type == "自定义规则":
            if hasattr(backtest_config, 'default_custom_rules'):
                global_config['custom_rules'] = backtest_config.default_custom_rules
            else:
                global_config['custom_rules'] = {
                    'open_rule': self.session_state.get('global_open_rule', ''),
                    'close_rule': self.session_state.get('global_close_rule', ''),
                    'buy_rule': self.session_state.get('global_buy_rule', ''),
                    'sell_rule': self.session_state.get('global_sell_rule', '')
                }

        return global_config

    def _get_individual_config(self, symbol: str, backtest_config) -> Optional[Dict[str, Any]]:
        """
        获取标的的个别配置

        Args:
            symbol: 标的代码
            backtest_config: 回测配置对象

        Returns:
            个别配置字典或None（如果没有个别配置）
        """
        # 检查是否有自定义配置
        if not self.session_state.get(f"{symbol}_has_custom_config", False):
            return None

        # 从策略映射中获取配置
        if hasattr(backtest_config, 'strategy_mapping') and symbol in backtest_config.strategy_mapping:
            mapping = backtest_config.strategy_mapping[symbol]
        else:
            # 从session state中获取配置
            strategy_type = self.session_state.get(f"strategy_type_{symbol}", "月定投")
            mapping = {'type': strategy_type}

            if strategy_type == "自定义规则":
                mapping['rules'] = {
                    'open_rule': self.session_state.get(f"open_rule_{symbol}", ""),
                    'close_rule': self.session_state.get(f"close_rule_{symbol}", ""),
                    'buy_rule': self.session_state.get(f"buy_rule_{symbol}", ""),
                    'sell_rule': self.session_state.get(f"sell_rule_{symbol}", "")
                }

        if mapping:
            individual_config = {
                'strategy_type': mapping.get('type', '月定投'),
                'source': 'individual_config'
            }

            if mapping.get('type') == "自定义规则" and 'rules' in mapping:
                individual_config['custom_rules'] = mapping['rules']

            return individual_config

        return None

    def _apply_inheritance(self, symbol: str, global_default: Dict[str, Any],
                          individual_config: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """
        应用继承逻辑，获取标的的有效配置

        Args:
            symbol: 标的代码
            global_default: 全局默认配置
            individual_config: 个别配置（可能为None）

        Returns:
            有效配置字典
        """
        if individual_config:
            # 有个别配置，使用个别配置
            effective_config = individual_config.copy()
            effective_config['inheritance_applied'] = True
            effective_config['inheritance_source'] = 'individual'
            effective_config['override_global'] = True
        else:
            # 没有个别配置，使用全局默认
            effective_config = global_default.copy()
            effective_config['inheritance_applied'] = True
            effective_config['inheritance_source'] = 'global_default'
            effective_config['override_global'] = False

        # 添加元数据
        effective_config['symbol'] = symbol
        effective_config['has_individual_config'] = individual_config is not None

        return effective_config

    def validate_strategy_hierarchy(self) -> tuple[bool, str]:
        """
        验证策略继承层次的合法性

        Returns:
            (is_valid, error_message): 验证结果和错误信息
        """
        # 取消全局配置验证，只验证个别配置
        # # 检查全局配置
        # global_strategy_type = self.session_state.get('global_default_strategy_type', '')
        # if not global_strategy_type:
        #     return False, "未设置全局默认策略类型"

        # # 检查自定义规则配置
        # if global_strategy_type == "自定义规则":
        #     global_rules = [
        #         self.session_state.get('global_open_rule', '').strip(),
        #         self.session_state.get('global_close_rule', '').strip(),
        #         self.session_state.get('global_buy_rule', '').strip(),
        #         self.session_state.get('global_sell_rule', '').strip()
        #     ]

        #     if not any(global_rules):
        #         return False, "全局自定义策略模式下必须配置至少一个交易规则"

        # 检查个别配置
        custom_symbols = [k.replace('_has_custom_config', '') for k in self.session_state.keys()
                         if k.endswith('_has_custom_config') and self.session_state[k]]

        for symbol in custom_symbols:
            strategy_type = self.session_state.get(f"strategy_type_{symbol}", "")
            if not strategy_type:
                return False, f"标的 {symbol} 未设置策略类型"

            if strategy_type == "自定义规则":
                symbol_rules = [
                    self.session_state.get(f"open_rule_{symbol}", "").strip(),
                    self.session_state.get(f"close_rule_{symbol}", "").strip(),
                    self.session_state.get(f"buy_rule_{symbol}", "").strip(),
                    self.session_state.get(f"sell_rule_{symbol}", "").strip()
                ]

                if not any(symbol_rules):
                    return False, f"标的 {symbol} 的自定义策略模式下必须配置至少一个交易规则"

        return True, "策略继承层次验证通过"

    def get_inheritance_rules(self) -> Dict[str, Any]:
        """
        获取策略继承规则配置

        Returns:
            继承规则配置字典
        """
        return {
            'inheritance_priority': ['individual_config', 'global_default', 'system_default'],
            'global_default_strategy': self.session_state.get('global_default_strategy_type', '月定投'),
            'custom_symbols': [k.replace('_has_custom_config', '') for k in self.session_state.keys()
                             if k.endswith('_has_custom_config') and self.session_state[k]],
            'inheritance_enabled': True
        }

    def resolve_config_conflicts(self, conflicts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        解决配置冲突

        Args:
            conflicts: 冲突列表

        Returns:
            解决方案字典
        """
        resolution = {
            'resolved_conflicts': [],
            'unresolved_conflicts': [],
            'applied_resolutions': []
        }

        for conflict in conflicts:
            symbol = conflict.get('symbol', '')
            conflict_type = conflict.get('type', '')

            if conflict_type == 'strategy_type_mismatch':
                # 策略类型不匹配，优先使用个别配置
                individual_type = self.session_state.get(f"strategy_type_{symbol}", "")
                if individual_type:
                    resolution['resolved_conflicts'].append({
                        'symbol': symbol,
                        'type': conflict_type,
                        'resolution': f"使用个别配置策略类型: {individual_type}",
                        'applied_to': 'individual_config'
                    })
                    resolution['applied_resolutions'].append(f"{symbol}: 使用个别策略类型 {individual_type}")
                else:
                    resolution['unresolved_conflicts'].append(conflict)

            elif conflict_type == 'missing_rules':
                # 缺少规则，尝试从全局配置继承
                global_rules = {
                    'open_rule': self.session_state.get('global_open_rule', ''),
                    'close_rule': self.session_state.get('global_close_rule', ''),
                    'buy_rule': self.session_state.get('global_buy_rule', ''),
                    'sell_rule': self.session_state.get('global_sell_rule', '')
                }

                if any(global_rules.values()):
                    # 应用全局规则
                    for rule_type, rule_value in global_rules.items():
                        if rule_value.strip():
                            self.session_state[f"{rule_type}_{symbol}"] = rule_value

                    resolution['resolved_conflicts'].append({
                        'symbol': symbol,
                        'type': conflict_type,
                        'resolution': "从全局配置继承规则",
                        'applied_to': 'global_rules'
                    })
                    resolution['applied_resolutions'].append(f"{symbol}: 继承全局规则")
                else:
                    resolution['unresolved_conflicts'].append(conflict)

        return resolution

    def get_inheritance_summary(self) -> Dict[str, Any]:
        """
        获取策略继承摘要

        Returns:
            继承摘要字典
        """
        symbols = [k.replace('_has_custom_config', '') for k in self.session_state.keys()
                  if k.endswith('_has_custom_config')]

        total_symbols = len(symbols)
        custom_symbols = len([s for s in symbols if self.session_state.get(f"{s}_has_custom_config", False)])
        default_symbols = total_symbols - custom_symbols

        return {
            'total_symbols': total_symbols,
            'custom_configured_symbols': custom_symbols,
            'global_default_symbols': default_symbols,
            'global_strategy_type': self.session_state.get('global_default_strategy_type', '月定投'),
            'inheritance_mode': 'multi_asset' if total_symbols > 1 else 'single_asset',
            'has_global_custom_rules': self.session_state.get('global_default_strategy_type') == '自定义规则'
        }

    def export_inheritance_config(self) -> Dict[str, Any]:
        """
        导出继承配置

        Returns:
            可序列化的继承配置字典
        """
        config = {
            'version': '1.0',
            'global_default': {
                'strategy_type': self.session_state.get('global_default_strategy_type', '月定投'),
                'custom_rules': {
                    'open_rule': self.session_state.get('global_open_rule', ''),
                    'close_rule': self.session_state.get('global_close_rule', ''),
                    'buy_rule': self.session_state.get('global_buy_rule', ''),
                    'sell_rule': self.session_state.get('global_sell_rule', '')
                }
            },
            'individual_configs': {},
            'inheritance_rules': self.get_inheritance_rules()
        }

        # 收集个别配置
        symbols = [k.replace('_has_custom_config', '') for k in self.session_state.keys()
                  if k.endswith('_has_custom_config') and self.session_state[k]]

        for symbol in symbols:
            config['individual_configs'][symbol] = {
                'strategy_type': self.session_state.get(f"strategy_type_{symbol}", ""),
                'has_custom_config': True,
                'custom_rules': {
                    'open_rule': self.session_state.get(f"open_rule_{symbol}", ""),
                    'close_rule': self.session_state.get(f"close_rule_{symbol}", ""),
                    'buy_rule': self.session_state.get(f"buy_rule_{symbol}", ""),
                    'sell_rule': self.session_state.get(f"sell_rule_{symbol}", "")
                }
            }

        return config

    def import_inheritance_config(self, config: Dict[str, Any]) -> tuple[bool, str]:
        """
        导入继承配置

        Args:
            config: 继承配置字典

        Returns:
            (is_success, message): 导入结果和消息
        """
        try:
            # 验证配置版本
            if config.get('version') != '1.0':
                return False, "不支持的配置版本"

            # 导入全局默认配置
            global_default = config.get('global_default', {})
            if 'strategy_type' in global_default:
                self.session_state['global_default_strategy_type'] = global_default['strategy_type']

            if 'custom_rules' in global_default:
                rules = global_default['custom_rules']
                self.session_state['global_open_rule'] = rules.get('open_rule', '')
                self.session_state['global_close_rule'] = rules.get('close_rule', '')
                self.session_state['global_buy_rule'] = rules.get('buy_rule', '')
                self.session_state['global_sell_rule'] = rules.get('sell_rule', '')

            # 导入个别配置
            individual_configs = config.get('individual_configs', {})
            for symbol, symbol_config in individual_configs.items():
                self.session_state[f"{symbol}_has_custom_config"] = symbol_config.get('has_custom_config', True)

                if 'strategy_type' in symbol_config:
                    self.session_state[f"strategy_type_{symbol}"] = symbol_config['strategy_type']

                if 'custom_rules' in symbol_config:
                    rules = symbol_config['custom_rules']
                    self.session_state[f"open_rule_{symbol}"] = rules.get('open_rule', '')
                    self.session_state[f"close_rule_{symbol}"] = rules.get('close_rule', '')
                    self.session_state[f"buy_rule_{symbol}"] = rules.get('buy_rule', '')
                    self.session_state[f"sell_rule_{symbol}"] = rules.get('sell_rule', '')

            return True, "配置导入成功"

        except Exception as e:
            return False, f"配置导入失败: {str(e)}"