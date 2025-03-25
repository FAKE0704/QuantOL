import os
import asyncio
from abc import ABC, abstractmethod
import pandas as pd
import aiohttp
from typing import Dict, Optional

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

class APIDataSource(DataSource):
    """API数据源实现"""
    def __init__(self, api_key: str, base_url: str, max_retries: int = 3, cache_dir: Optional[str] = None):
        self.api_key = api_key
        self.base_url = base_url
        self.max_retries = max_retries
        self.cache_dir = cache_dir
        self.cache: Dict[str, pd.DataFrame] = {}
        
        # 创建缓存目录
        if cache_dir and not os.path.exists(cache_dir):
            os.makedirs(cache_dir)

    async def load_data(self, symbol: str, start_date: str, end_date: str, frequency: str) -> pd.DataFrame:
        """异步加载数据"""
        cache_key = f"{symbol}_{frequency}_{start_date}_{end_date}"
        
        # 首先检查内存缓存
        if cache_key in self.cache:
            return self.cache[cache_key]
            
        # 检查磁盘缓存
        if self.cache_dir:
            cache_file = os.path.join(self.cache_dir, f"{cache_key}.parquet")
            if os.path.exists(cache_file):
                df = pd.read_parquet(cache_file)
                self.cache[cache_key] = df
                return df

        # 从API获取数据
        url = f"{self.base_url}/data"
        params = {
            "symbol": symbol,
            "start_date": start_date,
            "end_date": end_date,
            "frequency": frequency
        }
        headers = {"Authorization": f"Bearer {self.api_key}"}

        async with aiohttp.ClientSession() as session:
            for attempt in range(self.max_retries):
                try:
                    async with session.get(url, params=params, headers=headers, timeout=10) as response:
                        response.raise_for_status()
                        data = await response.json()
                        df = self._transform_data(data)
                        
                        # 缓存数据
                        self.cache[cache_key] = df
                        if self.cache_dir:
                            df.to_parquet(cache_file)
                            
                        return df
                except Exception as e:
                    if attempt == self.max_retries - 1:
                        raise DataSourceError(f"Failed to load data after {self.max_retries} attempts") from e
                    await asyncio.sleep(2 ** attempt)  # 指数退避

    def save_data(self, data: pd.DataFrame, symbol: str, frequency: str) -> bool:
        """保存数据"""
        return False  # API数据源通常不支持保存

    def check_data_exists(self, symbol: str, frequency: str) -> bool:
        """检查数据是否存在"""
        return True  # 假设API总是可用

    def _transform_data(self, data: dict) -> pd.DataFrame:
        """标准化数据格式"""
        df = pd.DataFrame(data)
        df['date'] = pd.to_datetime(df['date'])
        df = df.rename(columns={
            'open': 'Open',
            'high': 'High',
            'low': 'Low',
            'close': 'Close',
            'volume': 'Volume'
        })
        return df[['date', 'Open', 'High', 'Low', 'Close', 'Volume']]
