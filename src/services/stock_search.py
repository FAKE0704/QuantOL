from functools import lru_cache
from core.data.database import DatabaseManager

class StockSearchService:
    """股票搜索服务"""
    
    def __init__(self):
        self.db = DatabaseManager()
        self.db._init_db()
    
    @lru_cache(maxsize=1)
    def get_all_stocks(self):
        """获取全部股票信息（带缓存）"""
        df = self.db.get_all_stocks()
        return [(row['code'], row['code_name']) for _, row in df.iterrows()]
    
    def search(self, query: str) -> list:
        """执行股票搜索"""
        return [f"{code} {name}" for code, name in self.get_all_stocks() 
                if query.lower() in name.lower() or query in code]
    
    def refresh_cache(self):
        """刷新股票缓存"""
        self.get_all_stocks.cache_clear()
