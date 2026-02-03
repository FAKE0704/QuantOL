"""RuleParser门面模块

重构后的RuleParser - 门面模式（向后兼容）
"""
from typing import Any, Dict, Optional, Tuple, Union
import pandas as pd

from .expression_context import ExpressionContext
from .cache_manager import RuleCacheManager
from .result_storage import ResultStorageManager
from .cross_sectional_ranker import CrossSectionalRanker
from .rule_evaluator import RuleEvaluator
from ..indicators import IndicatorService


class RuleParser:
    """重构后的RuleParser - 门面模式（向后兼容）

    通过组合各个专业组件，提供与原RuleParser相同的API接口。
    """

    def __init__(
        self,
        data_provider: pd.DataFrame,
        indicator_service: IndicatorService,
        portfolio_manager: Any = None,
        cross_sectional_context: Optional[Dict[str, Any]] = None
    ):
        """使用注入的组件初始化

        Args:
            data_provider: 提供OHLCV等市场数据的DataFrame
            indicator_service: 指标计算服务
            portfolio_manager: 投资组合管理器，用于获取COST、POSITION等变量
            cross_sectional_context: 横截面上下文，包含data_dict、current_symbol、current_timestamp
        """
        self.data = data_provider
        self.indicator_service = indicator_service
        self.portfolio_manager = portfolio_manager

        # 提取横截面上下文
        self.cross_sectional_context = cross_sectional_context or {}
        self.data_dict = self.cross_sectional_context.get('data_dict', {})
        self.current_symbol = self.cross_sectional_context.get('current_symbol')
        self.current_timestamp = self.cross_sectional_context.get('current_timestamp')

        # 初始化缓存管理器
        self.cache_manager = RuleCacheManager(max_size=1000)

        # 初始化结果存储管理器
        self.storage_manager = ResultStorageManager(data_provider)

        # 初始化横截面排名器
        self.ranker: Optional[CrossSectionalRanker] = None
        if self.data_dict:
            self.ranker = CrossSectionalRanker(
                data_dict=self.data_dict,
                current_index=0,
                current_symbol=self.current_symbol
            )

        # 初始化规则评估器
        self.evaluator = RuleEvaluator(
            indicator_service=indicator_service,
            cache_manager=self.cache_manager,
            storage_manager=self.storage_manager,
            ranker=self.ranker
        )

        # 向后兼容状态
        self.current_index = 0
        self.series_cache = {}
        self.value_cache = {}
        self.max_recursion_depth = 100
        self.recursion_counter = 0
        self.cache_hits = 0
        self.cache_misses = 0

    @staticmethod
    def validate_syntax(rule: str) -> Tuple[bool, str]:
        """验证规则语法（无数据依赖）

        Args:
            rule: 规则表达式字符串

        Returns:
            (验证结果, 错误信息)
        """
        import ast
        import logging

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

    def parse(self, rule: str, mode: str = 'rule') -> Union[bool, float]:
        """解析规则表达式（向后兼容API）

        Args:
            rule: 规则表达式字符串
            mode: 解析模式 ('rule'返回bool, 'ref'返回原始数值)

        Returns:
            规则评估结果(bool)或原始数值(float)
        """
        context = self._create_context()
        return self.evaluator.evaluate_at(rule, context, mode)

    def evaluate_at(self, rule: str, index: int) -> bool:
        """在指定K线位置评估规则（向后兼容API）

        Args:
            rule: 规则表达式字符串
            index: 数据索引位置

        Returns:
            规则评估结果(bool)
        """
        self.current_index = index
        self.recursion_counter = 0

        # 更新排名器索引
        if self.ranker:
            self.ranker.update_index(index)

        context = self._create_context()
        result = self.evaluator.evaluate_at(rule, context, 'rule')

        if not isinstance(result, bool):
            return bool(result)
        return result

    def clear_cache(self):
        """清除序列缓存（向后兼容API）"""
        self.cache_manager.clear_all()
        self.series_cache = {}
        self.value_cache = {}

    @property
    def cache_hit_rate(self) -> float:
        """获取缓存命中率（向后兼容API）"""
        return self.cache_manager.cache_hit_rate

    def _create_context(self) -> ExpressionContext:
        """从当前状态创建评估上下文

        Returns:
            评估上下文实例
        """
        return ExpressionContext(
            data=self.data,
            current_index=self.current_index,
            current_symbol=self.current_symbol,
            current_timestamp=self.current_timestamp,
            portfolio_manager=self.portfolio_manager,
            cross_sectional_data=self.data_dict if self.data_dict else None
        )

    # 向后兼容的内部方法
    def _save_rule_result(self, rule: str, result: bool):
        """保存规则结果（向后兼容）"""
        self.storage_manager.save_rule_result(rule, result, self.current_index)

    def _clean_rule_name(self, rule: str) -> str:
        """清理规则表达式用作列名（向后兼容）"""
        return self.storage_manager._clean_rule_name(rule)

    def _store_expression_result(self, node, result: Any, bool_only: bool = False):
        """存储表达式结果（向后兼容）"""
        from .ast_node_handler import ASTNodeHandler
        expr = ASTNodeHandler.node_to_expr(node)
        self.storage_manager.save_expression_result(
            expr, result, self.current_index, is_bool=bool_only
        )

    def get_or_create_series(self, expr: str) -> pd.Series:
        """获取或创建指标序列（向后兼容）"""
        if expr in self.series_cache:
            return self.series_cache[expr]

        # 解析表达式并计算序列
        import ast
        tree = ast.parse(expr, mode='eval')
        context = self._create_context()
        series = self.evaluator._eval(tree.body, context)

        if not isinstance(series, pd.Series):
            raise ValueError(f"表达式 '{expr}' 未返回序列")

        self.series_cache[expr] = series
        return series
