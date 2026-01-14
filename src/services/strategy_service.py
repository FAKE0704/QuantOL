"""策略类型管理服务"""

from typing import List
from src.database import get_db_adapter


class StrategyService:
    """策略类型管理服务"""

    def __init__(self):
        self.db = get_db_adapter()

    async def get_trading_strategies(self) -> List[dict]:
        """获取所有交易策略"""
        strategies = await self.db.get_strategies(category='trading')
        return [
            {
                'value': s['code'],
                'label': s['name'],
                'description': s['description'],
                'default_params': s.get('default_params')
            }
            for s in strategies
        ]

    async def get_position_strategies(self) -> List[dict]:
        """获取所有仓位策略"""
        strategies = await self.db.get_strategies(category='position')
        return [
            {
                'value': s['code'],
                'label': s['name'],
                'description': s['description'],
                'default_params': s.get('default_params')
            }
            for s in strategies
        ]


# 单例
strategy_service = StrategyService()
