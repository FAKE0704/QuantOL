from abc import ABC, abstractmethod
import pandas as pd
from typing import Optional

class DataSourceError(Exception):
    """数据源操作异常基类"""
    pass

class DataSource(ABC):
    """数据源抽象基类"""
    @abstractmethod
    async def load_data(self, symbol: str, start_date: str, end_date: str, frequency: str) -> pd.DataFrame:
        """加载数据"""
        pass
        
    @abstractmethod
    def save_data(self, data: pd.DataFrame, symbol: str, frequency: str) -> bool:
        """保存数据"""
        pass

    @abstractmethod
    def check_data_exists(self, symbol: str, frequency: str) -> bool:
        """检查数据是否存在"""
        pass
