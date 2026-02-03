"""规则评估上下文模块

提供不可变的规则评估上下文数据类，用于在评估过程中传递数据。
"""
from dataclasses import dataclass, field
from typing import Any, Dict, Optional
import pandas as pd


@dataclass
class ExpressionContext:
    """不可变的规则评估上下文

    Attributes:
        data: 提供OHLCV等市场数据的DataFrame
        current_index: 当前K线位置索引
        current_symbol: 当前标的代码（用于横截面排名）
        current_timestamp: 当前时间戳
        portfolio_manager: 投资组合管理器（用于获取COST、POSITION等变量）
        cross_sectional_data: 横截面数据字典 {symbol: DataFrame}
    """
    data: pd.DataFrame
    current_index: int
    current_symbol: Optional[str] = None
    current_timestamp: Optional[Any] = None
    portfolio_manager: Any = None
    cross_sectional_data: Optional[Dict[str, pd.DataFrame]] = None

    def with_index(self, new_index: int) -> 'ExpressionContext':
        """创建带有新索引的上下文副本

        Args:
            new_index: 新的索引位置

        Returns:
            新的上下文实例
        """
        return ExpressionContext(
            data=self.data,
            current_index=new_index,
            current_symbol=self.current_symbol,
            current_timestamp=self.current_timestamp,
            portfolio_manager=self.portfolio_manager,
            cross_sectional_data=self.cross_sectional_data
        )

    @property
    def data_dict(self) -> Dict[str, pd.DataFrame]:
        """获取横截面数据字典（向后兼容）"""
        return self.cross_sectional_data or {}

    @property
    def has_cross_sectional_data(self) -> bool:
        """检查是否有横截面数据"""
        return bool(self.cross_sectional_data)
