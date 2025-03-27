from typing import Dict
# from database import DatabaseManager

class Stock:
    """股票实体类，封装股票基础属性和常用操作"""
    
    def __init__(self, code: str, db_manager: 'DatabaseManager'):
        self.code = code
        self.db = db_manager
        self._info: Dict = self.db.get_stock_info(code) or {}
        
    def refresh(self) -> None:
        """刷新股票信息"""
        self._info = self.db.get_stock_info(self.code) or {}
        
    @property
    def name(self) -> str:
        """股票简称"""
        return self._info.get('code_name', '')
    
    @property
    def ipo_date(self) -> str:
        """上市日期 (YYYY-MM-DD)"""
        return self._info.get('ipo_date', '')
    
    @property
    def status(self) -> str:
        """当前状态：上市/退市/停牌"""
        return self._info.get('status', '')
    
    def __repr__(self) -> str:
        return f"<Stock {self.code}: {self.name}>"
