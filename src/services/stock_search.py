from functools import lru_cache
from core.data.database import DatabaseManager

class StockSearchService:
    """股票搜索服务"""
    
    def __init__(self, db: DatabaseManager):
        self.db = db

    async def get_all_stocks(self):
        """异步获取全部股票信息"""
        return await self.db.get_all_stocks()
    
    async def search(self, query: str) -> list:
        """异步执行股票搜索"""
        stocks = await self.get_all_stocks()
        return [f"{code} {name}" for code, name in stocks 
                if query.lower() in name.lower() or query in code]
    
    async def refresh_cache(self):
        """异步刷新股票缓存"""
        # 由于我们不再使用lru_cache，这里可以简单重新获取数据
        await self.get_all_stocks()
