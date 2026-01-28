"""横截面排名配置模块"""
from dataclasses import dataclass, field
from typing import Optional, Dict, Any


@dataclass
class RankingConfig:
    """横截面排名配置类

    支持基于因子的选股策略，通过横截面排名选择交易标的。

    Attributes:
        factor_expression: 因子表达式，如 "RSI(close, 14)" 或 "(close-SMA(close,20))/close"
        ranking_method: 排名方法，"descending"表示降序（值大的优先），"ascending"表示升序
        top_n: 选择前N名作为目标标的
        rebalance_frequency: 再平衡频率，支持 "daily", "weekly", "monthly"
        rebalance_day: 再平衡日，每周几(1-7)或每月第几天(1-31)
        min_price: 最低股价过滤条件（可选）
        min_volume: 最低成交量过滤条件（可选）
        max_position_percent: 单个标的最大仓位比例（0-1之间）
    """

    factor_expression: str
    ranking_method: str = "descending"
    top_n: int = 10
    rebalance_frequency: str = "monthly"
    rebalance_day: int = 1
    min_price: Optional[float] = None
    min_volume: Optional[int] = None
    max_position_percent: float = 0.1  # 每个标的最大10%仓位

    def __post_init__(self):
        """参数验证"""
        valid_methods = ["ascending", "descending"]
        if self.ranking_method not in valid_methods:
            raise ValueError(f"ranking_method 必须是 {valid_methods} 之一")

        valid_frequencies = ["daily", "weekly", "monthly"]
        if self.rebalance_frequency not in valid_frequencies:
            raise ValueError(f"rebalance_frequency 必须是 {valid_frequencies} 之一")

        if self.top_n <= 0:
            raise ValueError("top_n 必须大于0")

        if not (0 < self.max_position_percent <= 1):
            raise ValueError("max_position_percent 必须在0到1之间")

        # 验证再平衡日
        if self.rebalance_frequency == "weekly":
            if not (1 <= self.rebalance_day <= 7):
                raise ValueError("weekly模式下，rebalance_day必须在1-7之间（周一到周日）")
        elif self.rebalance_frequency == "monthly":
            if not (1 <= self.rebalance_day <= 31):
                raise ValueError("monthly模式下，rebalance_day必须在1-31之间")

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "factor_expression": self.factor_expression,
            "ranking_method": self.ranking_method,
            "top_n": self.top_n,
            "rebalance_frequency": self.rebalance_frequency,
            "rebalance_day": self.rebalance_day,
            "min_price": self.min_price,
            "min_volume": self.min_volume,
            "max_position_percent": self.max_position_percent
        }

    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> "RankingConfig":
        """从字典创建配置"""
        return cls(**config_dict)
