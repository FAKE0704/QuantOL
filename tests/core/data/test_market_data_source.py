import os
import sys
import pytest
from unittest.mock import AsyncMock, MagicMock
import pandas as pd
import asyncio

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, project_root)

from core.data.market_data_source import MarketDataSource

@pytest.fixture
def mock_db_conn():
    conn = MagicMock()
    conn.transaction.return_value = AsyncMock()
    conn.executemany = AsyncMock()
    conn.fetchval = AsyncMock(return_value=True)
    return conn

@pytest.mark.asyncio
async def test_load_data():
    source = MarketDataSource(api_key="test", base_url="http://test")
    source._fetch_data = AsyncMock(return_value=pd.DataFrame({
        'open': [1], 'high': [2], 'low': [3], 'close': [4], 'volume': [5]
    }))
    
    data = await source.load_data("TEST", "20200101", "20201231", "daily")
    assert not data.empty
    assert set(data.columns) == {'open', 'high', 'low', 'close', 'volume'}

@pytest.mark.asyncio
async def test_save_data(mock_db_conn):
    source = MarketDataSource(api_key="test", base_url="http://test", db_conn=mock_db_conn)
    test_data = pd.DataFrame({
        'Open': [1], 'High': [2], 'Low': [3], 'Close': [4], 'Volume': [5]
    })
    
    result = await source.save_data(test_data, "TEST", "daily")
    assert result is True
    mock_db_conn.executemany.assert_awaited_once()

def test_get_data():
    source = MarketDataSource(api_key="test", base_url="http://test")
    source.load_data = AsyncMock(return_value=pd.DataFrame({
        'open': [1], 'high': [2], 'low': [3], 'close': [4], 'volume': [5]
    }))
    
    data = source.get_data("TEST", ["open", "close"])
    assert not data.empty
    assert set(data.columns) == {'open', 'close'}

def test_check_data_exists(mock_db_conn):
    source = MarketDataSource(api_key="test", base_url="http://test", db_conn=mock_db_conn)
    exists = source.check_data_exists("TEST", "daily")
    assert exists is True

@pytest.mark.asyncio
async def test_fetch_yahoo_data():
    source = MarketDataSource(api_key="test", base_url="http://test")
    source._fetch_data = AsyncMock(return_value=pd.DataFrame({
        'open': [1], 'high': [2], 'low': [3], 'close': [4], 'volume': [5]
    }))
    
    data = await source.fetch_yahoo_data("TEST")
    assert not data.empty

@pytest.mark.asyncio
async def test_fetch_tushare_data():
    source = MarketDataSource(api_key="test", base_url="http://test")
    source._fetch_data = AsyncMock(return_value=pd.DataFrame({
        'open': [1], 'high': [2], 'low': [3], 'close': [4], 'volume': [5]
    }))
    
    data = await source.fetch_tushare_data("TEST")
    assert not data.empty