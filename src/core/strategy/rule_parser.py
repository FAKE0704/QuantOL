import ast
import operator as op
import sys  # 添加sys导入
import logging
from typing import Dict, Callable, Union, List, Tuple
from dataclasses import dataclass
import pandas as pd
import astunparse
from .indicators import IndicatorService  # 引入IndicatorService

@dataclass
class IndicatorFunction:
    """指标函数描述"""
    name: str
    func: Callable
    params: Dict[str, type]
    description: str

class RuleParser:
    """规则解析引擎核心类"""
    
    @staticmethod
    def validate_syntax(rule: str) -> Tuple[bool, str]:
        """验证规则语法（不依赖数据）
        Args:
            rule: 规则表达式字符串
        Returns:
            (验证结果, 错误信息)
        """
        try:
            if not rule.strip():
                return False, "规则不能为空"
            ast.parse(rule, mode='eval')
            return True, "语法正确"
        except SyntaxError as e:
            logging.error(f"规则语法错误: {str(e)}")
            return False, f"规则语法错误: {str(e)}"
        except Exception as e:
            logging.error(f"规则验证异常: {str(e)}")
            return False, f"规则验证异常: {str(e)}"
            
    """规则解析引擎核心类"""
    
    OPERATORS = {
        ast.Gt: op.gt, 
        ast.Lt: op.lt,
        ast.Eq: op.eq,
        ast.And: op.and_,
        ast.BitAnd: op.and_,
        ast.Or: op.or_,
        ast.Not: op.not_
    }
    
    def __init__(self, data_provider: pd.DataFrame, indicator_service: IndicatorService):
        """初始化解析器
        Args:
            data_provider: 提供OHLCV等市场数据的DataFrame
            indicator_service: 指标计算服务
        """
        self.data = data_provider
        self.indicator_service = indicator_service
        # 只保留REF指标的特殊处理
        self._indicators = {
            'REF': IndicatorFunction(
                name='REF',
                func=self._ref,
                params={'expr': str, 'period': int},
                description='引用前n期数据: REF(expr, period)'
            )
        }
        self.series_cache = {}  # 序列缓存字典
        self.value_cache = {}   # 值缓存字典
        self.current_index = 0  # 当前计算位置
        self.max_recursion_depth = 100  # 最大递归深度
        self.recursion_counter = 0     # 递归计数器
        self.cache_hits = 0            # 缓存命中统计
        self.cache_misses = 0          # 缓存未命中统计
    
    def evaluate_at(self, rule: str, index: int) -> bool:
        """在指定K线位置评估规则
        Args:
            rule: 规则表达式字符串
            index: 数据索引位置
        Returns:
            规则评估结果(bool)
        """
        self.current_index = index
        self.recursion_counter = 0  # 重置递归计数器
        result = self.parse(rule)
        if not isinstance(result, bool):
            return bool(result)
        return result
        
    def parse(self, rule: str, mode: str = 'rule') -> Union[bool, float]:
        """解析规则表达式
        Args:
            rule: 规则表达式字符串，如"(SMA(5) > SMA(20)) & (RSI(14) < 30)"
            mode: 解析模式 ('rule'返回bool, 'ref'返回原始数值)
        Returns:
            规则评估结果(bool)或原始数值(float)
        Raises:
            SyntaxError: 规则语法错误时抛出
            ValueError: 指标参数错误时抛出
            RecursionError: 递归深度超过限制时抛出
        """
        try:
            if not rule.strip():
                return False if mode == 'rule' else 0.0
            tree = ast.parse(rule, mode='eval')
            result = self._eval(tree.body)
            return bool(result) if mode == 'rule' else result
        except RecursionError:
            raise RecursionError("递归深度超过限制，请简化规则表达式")
        except Exception as e:
            raise SyntaxError(f"规则解析失败: {str(e)}") from e
        
    def clear_cache(self):
        """清除序列缓存"""
        self.series_cache = {}
    
    def get_or_create_series(self, expr: str) -> pd.Series:
        """获取或创建指标序列"""
        if expr in self.series_cache:
            return self.series_cache[expr]
        
        # 解析表达式并计算序列
        tree = ast.parse(expr, mode='eval')
        series = self._eval(tree.body)
        
        if not isinstance(series, pd.Series):
            raise ValueError(f"表达式 '{expr}' 未返回序列")
            
        self.series_cache[expr] = series
        return series
    
    def _node_to_expr(self, node) -> str:
        """将AST节点转换为表达式字符串"""
        return astunparse.unparse(node).strip()
            
    def _eval(self, node):
        """递归评估AST节点"""
        if isinstance(node, ast.Compare):
            left = self._eval(node.left)
            right = self._eval(node.comparators[0])
            return self.OPERATORS[type(node.ops[0])](left, right)
        elif isinstance(node, ast.BoolOp):
            return self._eval_bool_op(node)
        elif isinstance(node, ast.Call):
            return self._eval_function_call(node)
        elif isinstance(node, ast.Name):
            return self._eval_variable(node)
        elif isinstance(node, ast.BinOp):
            left = self._eval(node.left)
            right = self._eval(node.right)
            return self.OPERATORS[type(node.op)](left, right)
        elif isinstance(node, ast.Constant):
            return node.value
        else:
            raise ValueError(f"不支持的AST节点类型: {type(node)}")

    def _eval_bool_op(self, node) -> bool:
        """评估逻辑运算符"""
        values = [self._eval(v) for v in node.values]
        return self.OPERATORS[type(node.op)](*values)
    
    def _eval_variable(self, node) -> float:
        """评估变量(从数据源获取)"""
        if node.id not in self.data.columns:
            raise ValueError(f"数据中不存在列: {node.id}")
        value = self.data[node.id].iloc[self.current_index]
        if pd.isna(value):
            return 0.0  # 空值处理
        return float(value)
    
    def _eval_function_call(self, node):
        """评估指标函数调用"""
        # 检查递归深度
        self.recursion_counter += 1
        if self.recursion_counter > self.max_recursion_depth:
            raise RecursionError(f"递归深度超过限制 ({self.max_recursion_depth})")
            
        func_name = node.func.id
        
        # 特殊处理REF函数（需要解析器状态）
        if func_name == 'REF':
            if func_name not in self._indicators:
                raise ValueError(f"不支持的指标函数: {func_name}")
                
            indicator = self._indicators[func_name]
            
            if len(node.args) != 2:
                raise ValueError("REF需要2个参数 (REF(expr, period))")
                
            expr_node = node.args[0]
            period_node = node.args[1]
            
            # 获取表达式字符串
            expr_str = self._node_to_expr(expr_node)
            period = self._eval(period_node)
            
            if not isinstance(period, (int, float)):
                raise ValueError("REF周期必须是数字")
                
            return indicator.func(expr_str, int(period))
        
        # 其他指标函数委托给IndicatorService
        # 从第一个参数获取数据列名
        data_column = self._node_to_expr(node.args[0]).strip()
        # 移除可能的引号（兼容字符串字面量）
        if data_column.startswith('"') and data_column.endswith('"'):
            data_column = data_column[1:-1]
        elif data_column.startswith("'") and data_column.endswith("'"):
            data_column = data_column[1:-1]
            
        if data_column not in self.data.columns:
            raise ValueError(f"数据中不存在列: {data_column}")
        
        # 获取数据序列
        series = self.data[data_column]
        remaining_args = node.args[1:]
        
        # 生成缓存键：函数名+数据列+参数+当前索引
        remaining_args_str = [self._node_to_expr(arg) for arg in remaining_args]
        args_list = [data_column] + remaining_args_str
        args_str = ",".join(args_list)
        cache_key = f"{func_name}({args_str})@{self.current_index}"
            
        if cache_key in self.value_cache:
            self.cache_hits += 1
            return float(self.value_cache[cache_key])  # 确保返回float
        
        # 计算并缓存结果
        self.cache_misses += 1
        
        # 验证指标参数（特别是周期类参数）
        for arg_node in remaining_args:
            arg_value = self._eval(arg_node)
            if not isinstance(arg_value, (int, float)) or arg_value <= 0:
                raise ValueError(
                    f"函数 {func_name} 的参数必须是正数: {arg_value}"
                )
                
        # 检查数据长度是否满足指标计算要求
        min_required = self._get_min_data_requirement(
            func_name,
            *[self._eval(arg) for arg in remaining_args]
        )
        if self.current_index < min_required:
            return 0.0
            
        # 委托给IndicatorService计算指标（传递数据序列和剩余参数）
        try:
            result = self.indicator_service.calculate_indicator(
                func_name, 
                series,  # 传递具体数据序列而非整个DataFrame
                self.current_index,
                *[self._eval(arg) for arg in remaining_args]  # 评估所有参数
            )
        except AttributeError:
            raise ValueError(f"不支持的指标函数: {func_name}")
        
        # 使用统一的安全转换方法
        try:
            result_float = self._safe_convert_to_float(
                result, 
                f"函数 {func_name} 的返回值"
            )
        except ValueError as e:
            # 添加额外上下文信息后重新抛出
            raise ValueError(
                f"指标函数 {func_name} 值转换失败: {str(e)}"
            ) from e
        
        # 缓存并返回结果
        self.value_cache[cache_key] = result_float
        return result_float
    
        
    def _safe_convert_to_float(self, value: any, context: str = "") -> float:
        """安全转换为浮点数，包含详细错误处理
        Args:
            value: 需要转换的值
            context: 错误上下文描述
        Returns:
            转换后的浮点数(处理NaN为0.0)
        Raises:
            ValueError: 转换失败时抛出
        """
        # 处理NaN值
        if pd.isna(value):
            return 0.0
            
        # 检查复数类型
        if isinstance(value, complex):
            raise ValueError(f"复数类型无法转换: {value} ({context})")
            
        # 处理None值
        if value is None:
            return 0.0
            
        # 处理布尔值
        if isinstance(value, bool):
            return float(value)
            
        # 处理字符串
        if isinstance(value, str):
            try:
                return float(value)
            except ValueError:
                raise ValueError(f"字符串无法转换为浮点数: {value} ({context})")
        
        # 处理Series类型
        if isinstance(value, pd.Series):
            if self.current_index < len(value):
                value = value.iloc[self.current_index]
            else:
                value = value.iloc[-1]
        
        # 处理NumPy类型
        try:
            import numpy as np
            if isinstance(value, np.generic):
                value = value.item()
        except ImportError:
            pass
        
        # 处理可转换为float的类型
        if hasattr(value, '__float__'):
            try:
                return float(value)
            except (TypeError, ValueError) as e:
                raise ValueError(
                    f"类型转换失败: {type(value)} -> float (值: {value}, 上下文: {context})"
                ) from e
                
        # 处理numpy数值类型
        try:
            import numpy as np
            if isinstance(value, (np.number, np.bool_)):
                return float(value.item())
        except ImportError:
            pass
            
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
        if func_name == 'sma':
            return int(args[0]) if args else 1
        elif func_name == 'rsi':
            return int(args[0]) if args else 14
        elif func_name == 'macd':
            return max(int(args[0]) if len(args)>0 else 12,
                      int(args[1]) if len(args)>1 else 26,
                      int(args[2]) if len(args)>2 else 9)
        return 1  # 默认最小长度

    def _ref(self, expr: str, period: int) -> float:
        """引用前period期的指标值（保留在RuleParser中）"""
        print(f"DEBUG_REF: 开始计算REF(expr={expr}, period={period})")
        
        # 检查递归深度
        self.recursion_counter += 1
        if self.recursion_counter > self.max_recursion_depth:
            raise RecursionError(f"递归深度超过限制 ({self.max_recursion_depth})")
            
        if period < 0:
            raise ValueError("周期必须是非负数")
            
        # 保存当前索引
        original_index = self.current_index
        
        # 计算目标位置（确保在有效范围内）
        target_index = max(0, min(original_index - period, len(self.data)-1))
        
        # 回溯到历史位置计算表达式
        self.current_index = target_index
        print(f"DEBUG_REF: 解析表达式 '{expr}' (索引={target_index})")
        try:
            # 尝试从缓存获取 - 使用统一格式的缓存键
            cache_key = f"REF({expr},{period})@{original_index}"
            if cache_key in self.value_cache:
                return float(self.value_cache[cache_key])
                
            # 使用parse方法解析表达式（指定ref模式获取原始数值）
            print(f"DEBUG_REF: 解析表达式 '{expr}'")
            result = self.parse(expr, mode='ref')
            print(f"DEBUG_REF: 表达式结果: {result}")
            
            # 使用统一的安全转换方法
            try:
                result_numeric = self._safe_convert_to_float(
                    result,
                    f"REF表达式 '{expr}'"
                )
            except ValueError as e:
                raise ValueError(f"REF值转换失败: {str(e)}") from e
            else:
                self.value_cache[cache_key] = result_numeric
                return result_numeric
        except Exception as e:
            raise ValueError(f"REF函数计算失败: {str(e)}") from e
        finally:
            # 恢复原始位置
            self.current_index = original_index
            self.recursion_counter -= 1  # 减少递归计数器
