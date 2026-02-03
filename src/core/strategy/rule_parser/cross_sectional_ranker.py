"""横截面排名模块

提供横截面排名逻辑，用于计算当前符号在所有符号中的排名。
"""
from typing import Dict, Optional
import pandas as pd


class CrossSectionalRanker:
    """横截面排名逻辑

    计算当前符号的field值在所有符号中的排名。
    """

    def __init__(
        self,
        data_dict: Dict[str, pd.DataFrame],
        current_index: int,
        current_symbol: Optional[str] = None
    ):
        """初始化横截面排名器

        Args:
            data_dict: 横截面数据字典 {symbol: DataFrame}
            current_index: 当前索引位置
            current_symbol: 当前标的代码
        """
        self.data_dict = data_dict
        self.current_index = current_index
        self.current_symbol = current_symbol

    def rank(self, field: str) -> int:
        """计算当前符号的排名

        Args:
            field: 字段名，如 'close', 'volume', 'high' 等

        Returns:
            排名（1=最高值，2=第二高，...），无数据时返回0
        """
        if not self.data_dict or not self.current_symbol:
            return 0  # 无横截面数据时返回0

        # 获取当前时间点所有股票的field值
        values = {}
        for symbol, data in self.data_dict.items():
            value = self._get_field_value_at_current_time(symbol, field)
            if value is not None and not pd.isna(value):
                values[symbol] = value

        if not values:
            return 0

        # 排名（降序：值越大排名越前）
        sorted_values = sorted(values.items(), key=lambda x: x[1], reverse=True)
        for rank, (symbol, _) in enumerate(sorted_values, 1):
            if symbol == self.current_symbol:
                return rank

        return 0

    def _get_field_value_at_current_time(
        self,
        symbol: str,
        field: str
    ) -> Optional[float]:
        """获取指定股票在当前时间点的字段值

        Args:
            symbol: 股票代码
            field: 字段名

        Returns:
            字段值，不存在或无数据时返回None
        """
        data = self.data_dict.get(symbol)
        if data is None:
            return None

        # 通过 current_index 获取当前行
        if 0 <= self.current_index < len(data):
            return data.at[data.index[self.current_index], field]
        return None

    def with_index(self, new_index: int) -> 'CrossSectionalRanker':
        """创建带有新索引的排名器副本

        Args:
            new_index: 新的索引位置

        Returns:
            新的排名器实例
        """
        return CrossSectionalRanker(
            data_dict=self.data_dict,
            current_index=new_index,
            current_symbol=self.current_symbol
        )

    def update_index(self, new_index: int) -> None:
        """更新当前索引位置

        Args:
            new_index: 新的索引位置
        """
        self.current_index = new_index

    def update_symbol(self, new_symbol: str) -> None:
        """更新当前标的代码

        Args:
            new_symbol: 新的标的代码
        """
        self.current_symbol = new_symbol
