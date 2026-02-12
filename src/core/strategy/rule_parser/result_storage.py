"""结果存储管理模块

提供DataFrame列存储管理功能，用于存储规则评估结果。
"""
import re
from typing import Any, Optional
import pandas as pd
from src.support.log.logger import logger


class ResultStorageManager:
    """DataFrame列存储管理

    负责将规则评估结果和中间表达式结果存储到DataFrame列中。
    """

    def __init__(self, data: pd.DataFrame):
        """初始化结果存储管理器

        Args:
            data: 目标DataFrame
        """
        self.data = data

    def save_rule_result(self, rule: str, result: bool, index: int) -> None:
        """保存规则评估结果到DataFrame列

        Args:
            rule: 规则表达式
            result: 规则评估结果
            index: 当前索引位置
        """
        try:
            # 清理规则表达式作为列名
            clean_rule = self._clean_rule_name(rule)

            # 如果列不存在，初始化为全False
            if clean_rule not in self.data.columns:
                self.data[clean_rule] = False

            # 在当前索引位置保存结果
            if 0 <= index < len(self.data):
                old_value = self.data.at[index, clean_rule]
                self.data.at[index, clean_rule] = result

                # 调试信息
                logger.debug(
                    f"保存规则结果: {clean_rule}[{index}] = {result} "
                    f"(原值: {old_value})"
                )

                # 保存表达式信息到attrs属性中
                if not hasattr(self.data, 'attrs'):
                    self.data.attrs = {}
                self.data.attrs[f"{clean_rule}_expr"] = rule
            else:
                logger.warning(
                    f"索引超出范围: {index} >= {len(self.data)}"
                )

        except Exception as e:
            logger.warning(
                f"保存规则结果失败: {str(e)}, 规则: {rule}"
            )

    def save_expression_result(
        self,
        expr: str,
        result: Any,
        index: int,
        is_bool: bool = False
    ) -> None:
        """保存中间表达式结果

        Args:
            expr: 表达式字符串
            result: 计算结果
            index: 当前索引位置
            is_bool: 是否为布尔表达式
        """
        # 不存储数字常量（如-5）作为列
        if self._is_numeric_constant(expr):
            return

        # 生成列名
        col_name = expr

        # 检查列是否已存在
        if col_name not in self.data.columns:
            # 根据表达式类型初始化列
            if is_bool:
                self.data[col_name] = [False] * len(self.data)
            else:
                self.data[col_name] = [float('nan')] * len(self.data)

            # 添加表达式注释
            if not hasattr(self.data, 'attrs'):
                self.data.attrs = {}
            self.data.attrs[f"{col_name}_expr"] = expr
            # 标记是否为关键表达式
            self.data.attrs[f"{col_name}_is_key"] = self.is_key_expression(expr)

        # 存储结果
        if 0 <= index < len(self.data):
            self.data.at[index, col_name] = bool(result) if is_bool else result

    def is_key_expression(self, expr: str) -> bool:
        """判断表达式是否为关键中间步骤

        关键表达式定义：
        1. 函数调用（如 SMA(close,5)、Z_SCORE(...)）
        2. 比较运算（如 close > SMA(...)）
        3. 特殊变量（COST、POSITION）
        4. 包含函数调用的复杂表达式

        非关键表达式：
        - 仅包含基本列的算术运算（如 close-low、open**5）

        Args:
            expr: 表达式字符串

        Returns:
            是否为关键表达式
        """
        # 函数调用是关键
        if re.search(r'[A-Z_]+\(', expr):
            return True
        # 比较运算是关键
        if re.search(r'\s*(>|<|==|>=|<=)\s', expr):
            return True
        # 特殊变量是关键
        if expr in ['COST', 'POSITION']:
            return True
        return False

    def save_variable_result(
        self,
        var_name: str,
        result: Any,
        index: int
    ) -> None:
        """保存特殊变量（如COST、POSITION）的结果

        Args:
            var_name: 变量名
            result: 变量值
            index: 当前索引位置
        """
        if var_name not in ['COST', 'POSITION']:
            return

        # 为特定变量创建单独的列
        if var_name not in self.data.columns:
            self.data[var_name] = [float('nan')] * len(self.data)
            if not hasattr(self.data, 'attrs'):
                self.data.attrs = {}
            self.data.attrs[f"{var_name}_expr"] = var_name
            # 特殊变量是关键表达式
            self.data.attrs[f"{var_name}_is_key"] = True

        if 0 <= index < len(self.data):
            # 即使result为0或None也存储
            self.data.at[index, var_name] = result if result is not None else float('nan')

    def save_indicator_result(
        self,
        func_name: str,
        args_str: str,
        result: float,
        index: int
    ) -> None:
        """保存指标计算结果

        Args:
            func_name: 指标函数名
            args_str: 参数字符串
            result: 计算结果
            index: 当前索引位置
        """
        col_name_raw = f"{func_name}({args_str})"
        col_name = self._clean_rule_name(col_name_raw)

        # 检查列是否已存在
        col_exists = (
            col_name in self.data.columns and
            hasattr(self.data, 'attrs') and
            f"{col_name}_expr" in self.data.attrs
        )

        if not col_exists:
            # 初始化列并填充NaN
            self.data[col_name] = [float('nan')] * len(self.data)
            # 添加表达式注释
            if not hasattr(self.data, 'attrs'):
                self.data.attrs = {}
            self.data.attrs[f"{col_name}_expr"] = f"{func_name}({args_str})"
            # 指标函数调用是关键表达式
            self.data.attrs[f"{col_name}_is_key"] = True

        # 确保当前索引有效
        if 0 <= index < len(self.data):
            self.data.at[index, col_name] = result
        else:
            logger.error(f"无效索引 {index} 无法存储指标 {col_name}")

    def _clean_rule_name(self, rule: str) -> str:
        """清理规则表达式用作列名

        只替换真正不能作为 DataFrame 列名的字符（如括号、逗号等），
        保留运算符符号以增强可读性。

        Args:
            rule: 原始规则表达式

        Returns:
            清理后的列名
        """
        # 只替换真正不兼容的字符（括号、大括号、引号、冒号等）
        # 保留运算符：+ - * / ^ % < > = ! & | ~ 和逗号
        clean_rule = re.sub(r'[(){}\[\]:"\'`]', '_', rule)
        # 替换空格为下划线（但保留比较运算符周围的空格）
        # 实际上，为了 DataFrame 兼容性，所有空格都替换为下划线
        clean_rule = re.sub(r'\s+', '_', clean_rule)
        # 移除多余的下划线
        clean_rule = re.sub(r'_+', '_', clean_rule)
        # 移除首尾下划线
        clean_rule = clean_rule.strip('_')

        return clean_rule

    @staticmethod
    def _is_numeric_constant(expr: str) -> bool:
        """判断表达式是否为数字常量

        Args:
            expr: 表达式字符串

        Returns:
            是否为数字常量
        """
        try:
            float(expr)
            return True
        except (ValueError, TypeError):
            return False

    def ensure_column_exists(
        self,
        col_name: str,
        expr: str,
        is_bool: bool = False
    ) -> None:
        """确保列存在，不存在则创建

        Args:
            col_name: 列名
            expr: 表达式（用于attrs注释）
            is_bool: 是否为布尔列
        """
        if col_name not in self.data.columns:
            if is_bool:
                self.data[col_name] = [False] * len(self.data)
            else:
                self.data[col_name] = [float('nan')] * len(self.data)

            if not hasattr(self.data, 'attrs'):
                self.data.attrs = {}
            self.data.attrs[f"{col_name}_expr"] = expr
