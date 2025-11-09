"""
配置验证服务
提供策略配置的验证功能
"""
from typing import Dict, Any, List, Tuple
import re


class ConfigValidationService:
    """配置验证服务"""

    def __init__(self):
        self.validation_rules = {
            'strategy_types': ["月定投", "移动平均线交叉", "MACD交叉", "RSI超买超卖", "自定义规则"],
            'required_rules_for_custom': ['open_rule', 'close_rule', 'buy_rule', 'sell_rule']
        }

    def validate_strategy_config(self, config: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        验证策略配置

        Args:
            config: 策略配置字典

        Returns:
            (is_valid, error_messages): 验证结果和错误信息列表
        """
        errors = []

        # 验证策略类型
        strategy_type = config.get('strategy_type', '')
        if not strategy_type:
            errors.append("策略类型不能为空")
        elif strategy_type not in self.validation_rules['strategy_types']:
            errors.append(f"无效的策略类型: {strategy_type}")

        # 验证自定义规则
        if strategy_type == "自定义规则":
            custom_rules = config.get('custom_rules', {})
            rule_errors = self._validate_custom_rules(custom_rules)
            errors.extend(rule_errors)

        return len(errors) == 0, errors

    def _validate_custom_rules(self, custom_rules: Dict[str, str]) -> List[str]:
        """
        验证自定义规则

        Args:
            custom_rules: 自定义规则字典

        Returns:
            错误信息列表
        """
        errors = []

        # 检查是否至少配置了一个规则
        has_any_rule = any([
            custom_rules.get('open_rule', '').strip(),
            custom_rules.get('close_rule', '').strip(),
            custom_rules.get('buy_rule', '').strip(),
            custom_rules.get('sell_rule', '').strip()
        ])

        if not has_any_rule:
            errors.append("自定义策略模式下必须配置至少一个交易规则")
            return errors

        # 验证规则语法
        for rule_name, rule_content in custom_rules.items():
            if rule_content.strip():
                syntax_errors = self._validate_rule_syntax(rule_content, rule_name)
                errors.extend(syntax_errors)

        return errors

    def _validate_rule_syntax(self, rule: str, rule_name: str) -> List[str]:
        """
        验证规则语法

        Args:
            rule: 规则内容
            rule_name: 规则名称

        Returns:
            错误信息列表
        """
        errors = []

        # 基本语法检查
        if not rule.strip():
            return errors

        # 检查是否包含基本的价格或指标引用
        has_price_reference = bool(re.search(r'\b(close|open|high|low)\b', rule, re.IGNORECASE))
        has_indicator_reference = bool(re.search(r'\b(ma|ema|rsi|macd|bb)\b', rule, re.IGNORECASE))

        if not (has_price_reference or has_indicator_reference):
            errors.append(f"{rule_name}: 规则应包含价格或技术指标引用")

        # 检查操作符
        has_operator = bool(re.search(r'[><=!]+', rule))
        if not has_operator:
            errors.append(f"{rule_name}: 规则应包含比较操作符 (>, <, >=, <=, ==, !=)")

        # 检查潜在的语法错误
        if re.search(r'[+\-*/]{2,}', rule):
            errors.append(f"{rule_name}: 包含连续的操作符")

        if rule.count('(') != rule.count(')'):
            errors.append(f"{rule_name}: 括号不匹配")

        return errors

    def validate_multi_asset_config(self, global_config: Dict[str, Any],
                                  individual_configs: Dict[str, Dict[str, Any]]) -> Tuple[bool, List[str]]:
        """
        验证多标配置

        Args:
            global_config: 全局配置
            individual_configs: 个别配置字典

        Returns:
            (is_valid, error_messages): 验证结果和错误信息列表
        """
        errors = []

        # 验证全局配置
        global_valid, global_errors = self.validate_strategy_config(global_config)
        if not global_valid:
            errors.extend([f"全局配置错误: {error}" for error in global_errors])

        # 验证个别配置
        for symbol, config in individual_configs.items():
            individual_valid, individual_errors = self.validate_strategy_config(config)
            if not individual_valid:
                errors.extend([f"标的 {symbol} 配置错误: {error}" for error in individual_errors])

        # 验证配置一致性
        consistency_errors = self._validate_config_consistency(global_config, individual_configs)
        errors.extend(consistency_errors)

        return len(errors) == 0, errors

    def _validate_config_consistency(self, global_config: Dict[str, Any],
                                   individual_configs: Dict[str, Dict[str, Any]]) -> List[str]:
        """
        验证配置一致性

        Args:
            global_config: 全局配置
            individual_configs: 个别配置字典

        Returns:
            错误信息列表
        """
        errors = []

        # 检查是否有重复的配置冲突
        for symbol, config in individual_configs.items():
            if config.get('strategy_type') == global_config.get('strategy_type'):
                # 如果策略类型相同，检查自定义规则是否也相同
                global_rules = global_config.get('custom_rules', {})
                individual_rules = config.get('custom_rules', {})

                if global_rules == individual_rules:
                    # 这里只是警告，不是错误
                    pass

        return errors

    def validate_strategy_inheritance(self, inheritance_config: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        验证策略继承配置

        Args:
            inheritance_config: 继承配置

        Returns:
            (is_valid, error_messages): 验证结果和错误信息列表
        """
        errors = []

        # 取消全局配置验证
        # # 验证继承优先级
        # priority = inheritance_config.get('inheritance_priority', [])
        # if len(priority) != 3:
        #     errors.append("继承优先级配置不完整")

        # expected_priorities = ['individual_config', 'global_default', 'system_default']
        # for expected in expected_priorities:
        #     if expected not in priority:
        #         errors.append(f"缺少必要的继承优先级: {expected}")

        # # 验证全局默认策略
        # global_strategy = inheritance_config.get('global_default_strategy', '')
        # if not global_strategy:
        #     errors.append("全局默认策略类型不能为空")

        # 验证自定义标的是否有效
        custom_symbols = inheritance_config.get('custom_symbols', [])
        if not isinstance(custom_symbols, list):
            errors.append("自定义标的配置格式错误")

        return len(errors) == 0, errors

    def get_validation_summary(self, validation_results: List[Tuple[bool, List[str]]]) -> Dict[str, Any]:
        """
        获取验证结果摘要

        Args:
            validation_results: 验证结果列表

        Returns:
            验证摘要字典
        """
        total_validations = len(validation_results)
        passed_validations = sum(1 for is_valid, _ in validation_results if is_valid)
        failed_validations = total_validations - passed_validations

        all_errors = []
        for is_valid, errors in validation_results:
            if not is_valid:
                all_errors.extend(errors)

        return {
            'total_validations': total_validations,
            'passed_validations': passed_validations,
            'failed_validations': failed_validations,
            'success_rate': passed_validations / total_validations if total_validations > 0 else 0,
            'all_errors': all_errors,
            'status': 'passed' if failed_validations == 0 else 'failed'
        }