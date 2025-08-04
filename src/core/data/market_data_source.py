from abc import ABC
from typing import Optional, Dict, List, Any, AsyncContextManager
import logging
from datetime import datetime
import pandas as pd
import aiohttp
import asyncio
from typing_extensions import Protocol
from .data_source import DataSource

class DatabaseConnection(Protocol):
    """数据库连接协议"""
    def transaction(self) -> AsyncContextManager[Any]:
        """返回异步上下文管理器"""
        ...
    async def executemany(self, query: str, params: List[Any]) -> None:
        """批量执行SQL"""
        ...
    async def fetchval(self, query: str, *args) -> Any:
        """获取单个值"""
        ...

class MarketDataSource(DataSource):
    """
    市场数据源实现类
    继承自DataSource抽象基类
    支持Yahoo/Tushare等多种数据源
    """
    
    def __init__(self, api_key: str, base_url: str, db_conn: Optional[DatabaseConnection] = None):
        self.api_key = api_key
        self.base_url = base_url
        self.db_conn = db_conn
        self.logger = logging.getLogger(__name__)
        
    async def load_data(self, symbol: str, start_date: str, end_date: str, frequency: str) -> pd.DataFrame:
        """实现DataSource抽象方法 - 加载数据"""
        params = {
            'start_date': start_date,
            'end_date': end_date,
            'frequency': frequency
        }
        return await self.fetch_tushare_data(symbol, **params)
        
    async def fetch_yahoo_data(self, symbol: str, **params) -> pd.DataFrame:
        """Yahoo Finance数据获取实现"""
        url = f"{self.base_url}/yahoo"
        return await self._fetch_data(url, symbol, params)
        
    async def fetch_tushare_data(self, symbol: str, **params) -> pd.DataFrame:
        """Tushare数据获取实现"""
        url = f"{self.base_url}/tushare"
        return await self._fetch_data(url, symbol, params)
        
    async def _fetch_data(self, url: str, symbol: str, params: dict) -> pd.DataFrame:
        """统一数据获取方法"""
        try:
            async with aiohttp.ClientSession() as session:
                params.update({"symbol": symbol, "token": self.api_key})
                async with session.get(url, params=params) as resp:
                    if resp.status != 200:
                        raise ValueError(f"API请求失败: {resp.status}")
                    data = await resp.json()
                    return pd.DataFrame(data)
        except Exception as e:
            self.logger.error(f"获取{symbol}数据失败: {e}")
            raise

    def save_data(self, data: pd.DataFrame, symbol: str, frequency: str) -> bool:
        """实现DataSource抽象方法 - 保存数据"""
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(self._save_to_db(data, symbol, frequency))
        
    async def _save_to_db(self, data: pd.DataFrame, symbol: str, frequency: str) -> bool:
        """保存数据到数据库"""
        if not self.db_conn:
            return False
            
        try:
            records = data.reset_index().to_dict('records')
            async with self.db_conn.transaction() as tx:
                await self.db_conn.executemany(
                    """
                    INSERT INTO market_data 
                    (symbol, date, open, high, low, close, volume, frequency)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                    ON CONFLICT (symbol, date, frequency) DO UPDATE SET
                        open = EXCLUDED.open,
                        high = EXCLUDED.high,
                        low = EXCLUDED.low,
                        close = EXCLUDED.close,
                        volume = EXCLUDED.volume
                    """,
                    [(symbol, 
                      r['date'], 
                      r['Open'], 
                      r['High'], 
                      r['Low'], 
                      r['Close'], 
                      r['Volume'],
                      frequency) for r in records]
                )
            return True
        except Exception as e:
            self.logger.error(f"保存数据到数据库失败: {e}")
            return False

    def check_data_exists(self, symbol: str, frequency: str) -> bool:
        """实现DataSource抽象方法 - 检查数据是否存在"""
        if not self.db_conn:
            return False
            
        try:
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(
                self.db_conn.fetchval(
                    "SELECT EXISTS(SELECT 1 FROM market_data WHERE symbol=$1 AND frequency=$2)",
                    symbol, frequency
                )
            )
        except Exception as e:
            self.logger.error(f"检查数据存在性失败: {e}")
            return False

    def get_available_fields(self, symbol: str) -> List[str]:
        """获取可用数据字段"""
        return ["open", "high", "low", "close", "volume", "turnover"]
        
    def get_data(self, symbol: str, fields: List[str]) -> pd.DataFrame:
        """兼容旧接口 - 同步获取市场数据"""
        try:
            loop = asyncio.get_event_loop()
            data = loop.run_until_complete(
                self.load_data(symbol=symbol,
                              start_date="",
                              end_date="",
                              frequency="daily")
            )
            return pd.DataFrame(data[fields])
        except Exception as e:
            self.logger.error(f"获取{symbol}数据失败: {e}")
            raise RuntimeError(f"无法获取{symbol}数据: {e}")