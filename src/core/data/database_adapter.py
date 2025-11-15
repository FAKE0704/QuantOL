from abc import ABC, abstractmethod
from typing import Any, Optional, List, Dict
import pandas as pd
from datetime import datetime, date, time
import os
from src.support.log.logger import logger


class DatabaseAdapter(ABC):
    """数据库适配器抽象基类"""

    @abstractmethod
    async def initialize(self) -> None:
        """初始化数据库连接和表结构"""
        pass

    @abstractmethod
    async def create_connection_pool(self) -> Any:
        """创建连接池"""
        pass

    @abstractmethod
    async def execute_query(self, query: str, *args) -> Any:
        """执行查询"""
        pass

    @abstractmethod
    async def close(self) -> None:
        """关闭连接"""
        pass

    @abstractmethod
    async def save_stock_info(self, code: str, code_name: str, ipo_date: str,
                             stock_type: str, status: str, out_date: Optional[str] = None) -> bool:
        """保存股票基本信息"""
        pass

    @abstractmethod
    async def check_data_completeness(self, symbol: str, start_date: date, end_date: date, frequency: str) -> list:
        """检查数据完整性"""
        pass

    @abstractmethod
    async def load_stock_data(self, symbol: str, start_date: date, end_date: date, frequency: str) -> pd.DataFrame:
        """加载股票数据"""
        pass

    @abstractmethod
    async def get_all_stocks(self) -> pd.DataFrame:
        """获取所有股票信息"""
        pass

    @abstractmethod
    async def get_stock_info(self, code: str) -> dict:
        """获取股票完整信息"""
        pass

    @abstractmethod
    async def get_stock_name(self, code: str) -> str:
        """根据股票代码获取名称"""
        pass

    @abstractmethod
    async def save_stock_data(self, symbol: str, data: pd.DataFrame, frequency: str) -> bool:
        """保存股票数据"""
        pass

    @abstractmethod
    async def save_money_supply_data(self, data: pd.DataFrame) -> bool:
        """保存货币供应量数据"""
        pass

    @abstractmethod
    async def get_money_supply_data(self, start_month: str, end_month: str) -> pd.DataFrame:
        """获取货币供应量数据"""
        pass

    @abstractmethod
    def get_pool_status(self) -> dict:
        """获取连接池状态"""
        pass