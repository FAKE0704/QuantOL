"""横截面排名模块

提供基于横截面排名的因子选股策略功能。

主要组件:
- RankingConfig: 排名配置类
- CrossSectionalRankingService: 横截面排名服务
- RankingBasedStrategy: 基于排名的策略
"""

from src.core.strategy.cross_sectional.ranking_config import RankingConfig
from src.core.strategy.cross_sectional.ranking_service import CrossSectionalRankingService
from src.core.strategy.cross_sectional.ranking_strategy import RankingBasedStrategy

__all__ = [
    "RankingConfig",
    "CrossSectionalRankingService",
    "RankingBasedStrategy"
]
