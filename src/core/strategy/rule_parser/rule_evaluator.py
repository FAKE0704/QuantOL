"""规则评估模块

提供表达式评估逻辑，处理规则解析和评估的核心功能。
"""
import ast
import logging
import math
from typing import Any, Union, Optional
import pandas as pd
import numpy as np

from .expression_context import ExpressionContext
from .cache_manager import RuleCacheManager
from .result_storage import ResultStorageManager
from .cross_sectional_ranker import CrossSectionalRanker
from .ast_node_handler import ASTNodeHandler
from src.core.strategy.indicators import IndicatorService
from src.support.log.logger import logger


class RuleEvaluator:
    """表达式评估逻辑（注入依赖）

    核心的规则评估类，负责解析和评估规则表达式。
    """

    def __init__(
        self,
        indicator_service: IndicatorService,
        cache_manager: RuleCacheManager,
        storage_manager: ResultStorageManager,
        ranker: Optional[CrossSectionalRanker] = None
    ):
        """初始化规则评估器

        Args:
            indicator_service: 指标计算服务
            cache_manager: 缓存管理器
            storage_manager: 结果存储管理器
            ranker: 横截面排名器（可选）
        """
        self.indicator_service = indicator_service
        self.cache_manager = cache_manager
        self.storage_manager = storage_manager
        self.ranker = ranker
        self.max_recursion_depth = 100
        self.recursion_counter = 0

    def evaluate_at(
        self,
        rule: str,
        context: ExpressionContext,
        mode: str = 'rule'
    ) -> Union[bool, float]:
        """在特定索引处评估规则

        Args:
            rule: 规则表达式字符串
            context: 评估上下文
            mode: 解析模式 ('rule'返回bool, 'ref'返回原始数值)

        Returns:
            规则评估结果(bool)或原始数值(float)

        Raises:
            RecursionError: 递归深度超过限制时抛出
            SyntaxError: 规则语法错误时抛出
        """
        try:
            if not rule.strip():
                return False if mode == 'rule' else 0.0

            tree = ast.parse(rule, mode='eval')
            self.recursion_counter = 0
            result = self._eval(tree.body, context)
            final_result = bool(result) if mode == 'rule' else result

            if mode == 'rule':
                self.storage_manager.save_rule_result(
                    rule, final_result, context.current_index
                )

            return final_result
        except RecursionError:
            raise RecursionError("递归深度超过限制，请简化规则表达式")
        except Exception as e:
            raise SyntaxError(f"规则解析失败: {str(e)}") from e

    def _eval(self, node: ast.AST, context: ExpressionContext) -> Any:
        """递归评估AST节点

        Args:
            node: AST节点
            context: 评估上下文

        Returns:
            评估结果
        """
        if isinstance(node, ast.Compare):
            return self._eval_compare(node, context)
        elif isinstance(node, ast.BoolOp):
            return self._eval_bool_op(node, context)
        elif isinstance(node, ast.Call):
            return self._eval_function_call(node, context)
        elif isinstance(node, ast.Name):
            return self._eval_variable(node, context)
        elif isinstance(node, ast.BinOp):
            return self._eval_bin_op(node, context)
        elif isinstance(node, ast.Constant):
            return self._eval_constant(node)
        elif isinstance(node, ast.UnaryOp):
            return self._eval_unary_op(node, context)
        else:
            raise ValueError(f"不支持的AST节点类型: {type(node)}")

    def _eval_compare(self, node: ast.Compare, context: ExpressionContext) -> bool:
        """评估比较运算

        Args:
            node: Compare节点
            context: 评估上下文

        Returns:
            比较结果
        """
        left = self._eval(node.left, context)
        right = self._eval(node.comparators[0], context)
        op_func = ASTNodeHandler.get_operator_func(type(node.ops[0]))
        result = op_func(left, right)

        # 存储比较运算结果
        self.storage_manager.save_expression_result(
            ASTNodeHandler.node_to_expr(node), result, context.current_index, is_bool=True
        )
        return result

    def _eval_bool_op(self, node: ast.BoolOp, context: ExpressionContext) -> bool:
        """评估逻辑运算符

        Args:
            node: BoolOp节点
            context: 评估上下文

        Returns:
            逻辑运算结果
        """
        values = [self._eval(v, context) for v in node.values]
        op_func = ASTNodeHandler.get_operator_func(type(node.op))
        result = op_func(*values)

        # 存储布尔运算结果
        self.storage_manager.save_expression_result(
            ASTNodeHandler.node_to_expr(node), result, context.current_index, is_bool=True
        )
        return result

    def _eval_bin_op(self, node: ast.BinOp, context: ExpressionContext) -> float:
        """评估二元运算

        Args:
            node: BinOp节点
            context: 评估上下文

        Returns:
            运算结果
        """
        left = self._eval(node.left, context)
        right = self._eval(node.right, context)

        # 处理除零错误
        if isinstance(node.op, (ast.Div, ast.FloorDiv)) and right == 0:
            expr_str = ASTNodeHandler.node_to_expr(node)
            # 特殊处理：对于COST/POSITION表达式，当POSITION为0时返回0.0
            if 'COST' in expr_str and 'POSITION' in expr_str:
                return 0.0
            return 0.0

        op_func = ASTNodeHandler.get_operator_func(type(node.op))
        result = op_func(left, right)

        # 存储二元运算结果
        self.storage_manager.save_expression_result(
            ASTNodeHandler.node_to_expr(node), result, context.current_index, is_bool=False
        )
        return result

    def _eval_unary_op(self, node: ast.UnaryOp, context: ExpressionContext) -> Any:
        """评估一元运算符

        Args:
            node: UnaryOp节点
            context: 评估上下文

        Returns:
            运算结果
        """
        operand = self._eval(node.operand, context)
        if isinstance(node.op, ast.USub):  # 负号
            return -operand
        elif isinstance(node.op, ast.UAdd):  # 正号
            return +operand
        elif isinstance(node.op, ast.Not):  # 逻辑非
            return not operand
        elif isinstance(node.op, ast.Invert):  # 按位取反 ~
            return ~int(operand) if operand is not None else None
        else:
            raise ValueError(f"不支持的一元运算符: {type(node.op)}")

    def _eval_constant(self, node: ast.Constant) -> float:
        """评估常量

        Args:
            node: Constant节点

        Returns:
            常量值
        """
        try:
            return float(node.value)
        except (TypeError, ValueError):
            return 0.0

    def _eval_variable(self, node: ast.Name, context: ExpressionContext) -> float:
        """评估变量(从数据源获取或从portfolio_manager获取)

        Args:
            node: Name节点
            context: 评估上下文

        Returns:
            变量值
        """
        var_name = node.id

        # 处理投资组合相关变量
        if var_name == 'COST' and context.portfolio_manager:
            result = context.portfolio_manager.get_total_cost()
            self.storage_manager.save_variable_result(
                var_name, result, context.current_index
            )
            return result
        elif var_name == 'POSITION' and context.portfolio_manager:
            # 需要从数据中获取当前标的代码
            if not context.data.empty and 'code' in context.data.columns:
                current_symbol = context.data['code'].iloc[context.current_index]
                position = context.portfolio_manager.get_position(current_symbol)
                result = position.quantity if position else 0.0
            else:
                result = 0.0
            self.storage_manager.save_variable_result(
                var_name, result, context.current_index
            )
            return result

        # 处理数据列变量
        if var_name not in context.data.columns:
            raise ValueError(f"数据中不存在列: {var_name}")
        value = context.data[var_name].iloc[context.current_index]
        if pd.isna(value):
            return 0.0
        return float(value)

    def _eval_function_call(self, node: ast.Call, context: ExpressionContext) -> float:
        """评估指标函数调用

        Args:
            node: Call节点
            context: 评估上下文

        Returns:
            函数计算结果
        """
        # 检查递归深度
        self.recursion_counter += 1
        if self.recursion_counter > self.max_recursion_depth:
            self.recursion_counter -= 1
            raise RecursionError(
                f"递归深度超过限制 ({self.max_recursion_depth})"
            )

        try:
            func_name = node.func.id.upper()
            args_str = ", ".join([
                ASTNodeHandler._node_to_expr_simple(arg) for arg in node.args
            ])

            # 特殊函数处理
            if func_name == 'REF':
                return self._eval_ref(node, context)
            elif func_name == 'Q':
                return self._eval_q(node, context)
            elif func_name == 'C_P':
                return self._eval_c_p(node, context)
            elif func_name == 'VWAP':
                return self._eval_vwap(node, context)
            elif func_name == 'SQRT':
                return self._eval_sqrt(node, context)
            elif func_name == 'RANK':
                return self._eval_rank(node, context)

            # 其他指标函数委托给IndicatorService
            return self._eval_indicator(node, context, func_name, args_str)

        finally:
            self.recursion_counter -= 1

    def _eval_ref(self, node: ast.Call, context: ExpressionContext) -> float:
        """评估REF函数

        Args:
            node: Call节点
            context: 评估上下文

        Returns:
            REF计算结果
        """
        if len(node.args) != 2:
            raise ValueError("REF需要2个参数 (REF(expr, period))")

        expr_node = node.args[0]
        period_node = node.args[1]

        expr_str = ASTNodeHandler.node_to_expr(expr_node)
        period = self._eval(period_node, context)

        if not isinstance(period, (int, float)):
            raise ValueError("REF周期必须是数字")

        period = int(period)
        if period < 0:
            raise ValueError("周期必须是非负数")

        # 先计算并存储原始指标
        if "(" in expr_str and ")" in expr_str:
            original_result = self.evaluate_at(expr_str, context, mode='ref')
            if expr_str not in context.data.columns:
                context.data[expr_str] = None
            context.data.at[context.current_index, expr_str] = original_result

        # 保存当前索引
        original_index = context.current_index

        # 计算目标位置
        target_index = max(0, min(int(original_index) - period, len(context.data) - 1))

        # 回溯到历史位置计算表达式
        new_context = context.with_index(target_index)

        try:
            # 尝试从缓存获取
            cache_key = self.cache_manager.get_time_dependent_key(
                "REF", original_index, expr_str, period
            )
            cached = self.cache_manager.get_time_cached(cache_key)
            if cached is not None:
                return float(cached)

            # 使用完整evaluate_at流程解析表达式
            result = self.evaluate_at(expr_str, new_context, mode='ref')

            # 处理结果并缓存
            result_numeric = self._safe_convert_to_float(
                result, f"REF表达式 '{expr_str}'"
            )

            # 缓存结果
            self.cache_manager.set_time_cached(cache_key, result_numeric)

            return result_numeric
        finally:
            # 恢复原始位置
            context.current_index = original_index

    def _eval_q(self, node: ast.Call, context: ExpressionContext) -> float:
        """评估Q函数（分位数计算）

        Args:
            node: Call节点
            context: 评估上下文

        Returns:
            分位数值
        """
        if len(node.args) != 3:
            raise ValueError("Q需要3个参数 (Q(series, quantile, period))")

        data_column = ASTNodeHandler.node_to_expr(node.args[0]).strip('\"\'')
        quantile_val = self._eval(node.args[1], context)
        period_val = self._eval(node.args[2], context)

        quantile = float(quantile_val) if isinstance(quantile_val, (int, float)) else 0.5
        period = int(period_val) if isinstance(period_val, (int, float)) else 5

        if not 0 <= quantile <= 1:
            raise ValueError(f"分位数必须在0到1之间，当前值: {quantile}")

        if period <= 0:
            raise ValueError(f"周期必须为正整数，当前值: {period}")

        # 检查数据长度是否满足周期要求
        if context.current_index < period - 1:
            result = float('nan')
        else:
            start_idx = int(context.current_index) - period + 1
            end_idx = int(context.current_index) + 1
            window_data = context.data[data_column].iloc[start_idx:end_idx]
            result = window_data.quantile(quantile)

        # 存储到列
        col_name = f"Q({data_column},{quantile},{period})"
        self.storage_manager.save_expression_result(
            col_name, result, context.current_index, is_bool=False
        )
        return result

    def _eval_c_p(self, node: ast.Call, context: ExpressionContext) -> float:
        """评估C_P函数: (REF(high, n)+REF(low, n))/2

        Args:
            node: Call节点
            context: 评估上下文

        Returns:
            C_P计算结果
        """
        if len(node.args) != 1:
            raise ValueError("C_P需要1个参数 (C_P(period))")

        period = self._eval(node.args[0], context)
        if not isinstance(period, (int, float)) or period < 0:
            raise ValueError("C_P周期必须是非负整数")

        period = int(period)

        # 检查数据长度是否足够
        if context.current_index < period:
            return 0.0

        try:
            # 计算C_P值
            high_ref = self._get_ref_value("high", period, context)
            low_ref = self._get_ref_value("low", period, context)
            return (high_ref + low_ref) / 2.0
        except Exception as e:
            logger.error(f"C_P计算失败: {str(e)}")
            return 0.0

    def _eval_vwap(self, node: ast.Call, context: ExpressionContext) -> float:
        """评估VWAP函数: 成交量加权平均价

        Args:
            node: Call节点
            context: 评估上下文

        Returns:
            VWAP计算结果
        """
        if len(node.args) != 1:
            raise ValueError("VWAP需要1个参数 (VWAP(period))")

        period = self._eval(node.args[0], context)
        if not isinstance(period, (int, float)) or period <= 0:
            raise ValueError("VWAP周期必须是正整数")

        period = int(period)

        # 检查数据长度是否足够
        if context.current_index < period:
            return float('nan')

        try:
            total_price_volume = 0.0
            total_volume = 0.0

            for i in range(period):
                # 计算当前期的C_P值
                high_ref = self._get_ref_value("high", i, context)
                low_ref = self._get_ref_value("low", i, context)
                cp_value = (high_ref + low_ref) / 2.0

                # 获取对应期的成交量
                volume_ref = self._get_ref_value("volume", i, context)

                total_price_volume += cp_value * volume_ref
                total_volume += volume_ref

            if total_volume == 0:
                return 0.0

            return total_price_volume / total_volume
        except Exception as e:
            logger.error(f"VWAP计算失败: {str(e)}")
            return 0.0

    def _eval_sqrt(self, node: ast.Call, context: ExpressionContext) -> float:
        """评估SQRT函数: 对x开n次方

        Args:
            node: Call节点
            context: 评估上下文

        Returns:
            SQRT计算结果
        """
        if len(node.args) != 2:
            raise ValueError("SQRT需要2个参数 (SQRT(x, n))")

        x_value = self._eval(node.args[0], context)
        n_value = self._eval(node.args[1], context)

        # 验证参数
        if not isinstance(x_value, (int, float)):
            raise ValueError("SQRT的第一个参数必须是数字")
        if not isinstance(n_value, (int, float)):
            raise ValueError("SQRT的第二个参数必须是数字")

        # 特殊处理：如果开偶数次方，底数不能为负数
        if int(n_value) % 2 == 0 and x_value < 0:
            logger.warning(f"SQRT: 负数{x_value}开偶数次方{n_value}，返回0.0")
            return 0.0

        # 如果n为0，返回1
        if n_value == 0:
            return 1.0

        try:
            # 使用数学公式：x^(1/n)
            result = math.pow(x_value, 1.0 / n_value)
            return float(result)
        except Exception as e:
            logger.error(f"SQRT计算失败: {str(e)}")
            return 0.0

    def _eval_rank(self, node: ast.Call, context: ExpressionContext) -> int:
        """评估RANK函数：横截面排名

        Args:
            node: Call节点
            context: 评估上下文

        Returns:
            排名值
        """
        if len(node.args) != 1:
            raise ValueError("RANK需要1个参数 (RANK(field))")

        if self.ranker is None:
            return 0

        # 更新排名器的索引
        self.ranker.update_index(context.current_index)
        if context.current_symbol:
            self.ranker.update_symbol(context.current_symbol)

        field = ASTNodeHandler.node_to_expr(node.args[0]).strip('\"\'')
        result = self.ranker.rank(field)

        # 存储结果
        self.storage_manager.save_expression_result(
            f"RANK({field})", result, context.current_index, is_bool=False
        )
        return result

    def _eval_indicator(
        self,
        node: ast.Call,
        context: ExpressionContext,
        func_name: str,
        args_str: str
    ) -> float:
        """评估普通指标函数

        Args:
            node: Call节点
            context: 评估上下文
            func_name: 函数名
            args_str: 参数字符串

        Returns:
            指标计算结果
        """
        # 从第一个参数获取数据列名
        data_column = ASTNodeHandler.node_to_expr(node.args[0]).strip()
        if data_column.startswith('"') and data_column.endswith('"'):
            data_column = data_column[1:-1]
        elif data_column.startswith("'") and data_column.endswith("'"):
            data_column = data_column[1:-1]

        if data_column not in context.data.columns:
            raise ValueError(f"数据中不存在列: {data_column}")

        # 获取数据序列
        series = context.data[data_column]
        remaining_args = node.args[1:]

        # 生成缓存键
        remaining_args_str = [
            ASTNodeHandler.node_to_expr(arg) for arg in remaining_args
        ]
        args_list = [data_column] + remaining_args_str
        args_str_full = ",".join(args_list)
        cache_key = self.cache_manager.get_time_dependent_key(
            func_name, context.current_index, args_str_full
        )

        # 检查缓存
        cached = self.cache_manager.get_time_cached(cache_key)
        if cached is not None:
            return float(cached)

        # 验证指标参数
        for arg_node in remaining_args:
            arg_value = self._eval(arg_node, context)
            if not isinstance(arg_value, (int, float)) or arg_value <= 0:
                raise ValueError(
                    f"函数 {func_name} 的参数必须是正数: {arg_value}"
                )

        # 检查数据长度是否满足指标计算要求
        min_required = self._get_min_data_requirement(
            func_name, *[self._eval(arg, context) for arg in remaining_args]
        )
        if context.current_index < min_required:
            return 0.0

        # 委托给IndicatorService计算指标
        try:
            current_index = int(context.current_index)
            result = self.indicator_service.calculate_indicator(
                func_name,
                series,
                current_index,
                *[self._eval(arg, context) for arg in remaining_args]
            )
        except AttributeError as e:
            logging.error(f"不支持的指标函数: {func_name}, 错误: {str(e)}")
            raise ValueError(f"不支持的指标函数: {func_name}") from e
        except Exception as e:
            logging.error(
                f"指标计算失败: {func_name}({args_str_full}), "
                f"错误: {str(e)}, 位置={context.current_index}"
            )
            raise

        # 转换为浮点数
        result_float = self._safe_convert_to_float(
            result, f"函数 {func_name} 的返回值"
        )

        # 缓存并存储结果
        self.cache_manager.set_time_cached(cache_key, result_float)
        self.storage_manager.save_indicator_result(
            func_name, args_str_full, result_float, context.current_index
        )

        return result_float

    def _get_ref_value(
        self,
        field: str,
        period: int,
        context: ExpressionContext
    ) -> float:
        """获取指定字段的REF值

        Args:
            field: 字段名
            period: 回溯周期
            context: 评估上下文

        Returns:
            REF值
        """
        if period < 0:
            raise ValueError("周期必须是非负数")

        target_index = max(0, context.current_index - period)
        if target_index >= len(context.data):
            return 0.0

        value = context.data[field].iloc[target_index]
        if pd.isna(value):
            return 0.0
        return float(value)

    def _safe_convert_to_float(self, value: Any, context: str = "") -> float:
        """安全转换为浮点数

        Args:
            value: 需要转换的值
            context: 错误上下文描述

        Returns:
            转换后的浮点数

        Raises:
            ValueError: 转换失败时抛出
        """
        # 处理NaN/None值
        if pd.isna(value) or value is None:
            return 0.0

        # 处理布尔值
        if isinstance(value, bool):
            return float(value)

        # 处理数字类型
        if isinstance(value, (int, float)):
            return float(value)

        # 处理字符串
        if isinstance(value, str):
            try:
                return float(value)
            except ValueError:
                raise ValueError(f"字符串无法转换为浮点数: {value} ({context})")

        # 处理Series类型
        if isinstance(value, pd.Series):
            index = context.current_index if hasattr(context, 'current_index') else -1
            if index < len(value):
                value = value.iloc[index]
            else:
                value = value.iloc[-1]
            return self._safe_convert_to_float(value, context)

        # 处理numpy类型
        if isinstance(value, (np.number, np.bool_, np.generic)):
            return float(value.item())

        # 处理可转换为float的类型
        if hasattr(value, '__float__'):
            try:
                return float(value)
            except (TypeError, ValueError) as e:
                raise ValueError(
                    f"类型转换失败: {type(value)} -> float (值: {value}, 上下文: {context})"
                ) from e

        raise ValueError(
            f"不支持的类型转换: {type(value)} -> float (值: {value}, 上下文: {context})"
        )

    def _get_min_data_requirement(self, func_name: str, *args) -> int:
        """获取指标函数的最小数据要求

        Args:
            func_name: 指标函数名
            *args: 指标参数

        Returns:
            最小需要的数据长度
        """
        func_name = func_name.lower()
        try:
            if func_name == 'sma':
                return int(float(args[0])) if args else 1
            elif func_name == 'rsi':
                return int(float(args[0])) if args else 14
            elif func_name == 'macd':
                return max(
                    int(float(args[0])) if len(args) > 0 else 12,
                    int(float(args[1])) if len(args) > 1 else 26,
                    int(float(args[2])) if len(args) > 2 else 9
                )
            elif func_name == 'c_p':
                return int(float(args[0])) if args else 0
            elif func_name == 'vwap':
                return int(float(args[0])) if args else 1
            elif func_name == 'sqrt':
                return 0
            elif func_name == 'std':
                return int(float(args[0])) if args else 2
            elif func_name in ('zscore', 'z_score'):
                return int(float(args[0])) if args else 2
            elif func_name == 'ema':
                return int(float(args[0])) if args else 2
            elif func_name == 'dif':
                long = int(float(args[1])) if len(args) > 1 else 26
                return long
            elif func_name == 'dea':
                long = int(float(args[2])) if len(args) > 2 else 26
                signal = int(float(args[0])) if args else 9
                return long + signal
            return 1
        except (ValueError, TypeError):
            return 1
