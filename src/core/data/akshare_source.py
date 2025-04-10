import akshare as ak
import pandas as pd
import streamlit as st
import logging
from datetime import datetime
from typing import Optional
from functools import lru_cache
from tenacity import retry, stop_after_attempt, wait_exponential
from .data_source import DataSource

logger = logging.getLogger(__name__)

class AkShareSource(DataSource):
    """AkShare数据源实现，遵循DataSource接口规范"""
    
    def check_data_exists(self, symbol: str, start_date: str, end_date: str) -> bool:
        """检查指定时间段的数据是否存在"""
        try:
            df = self.get_data(symbol, start_date, end_date)
            return not df.empty
        except Exception:
            return False
            
    async def load_data(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """异步加载数据"""
        return self.get_data(symbol, start_date, end_date)
        
    def save_data(self, symbol: str, data: pd.DataFrame) -> bool:
        """保存数据（AkShare为只读数据源，此方法仅用于接口兼容）"""
        return False
    
    def __init__(self):
        self._initialized = False
        self._field_mapping = {
            "日期": "date",
            "开盘": "open",
            "收盘": "close",
            "最高": "high",
            "最低": "low",
            "成交量": "volume",
            "成交额": "amount"
        }
        
    async def async_init(self):
        """异步初始化，验证依赖和连接"""
        try:
            # 测试一个简单请求验证akshare可用性
            ak.stock_zh_a_spot()
            self._initialized = True
        except Exception as e:
            logger.error(f"Akshare初始化失败: {str(e)}")
            raise RuntimeError("AkShare初始化失败，请检查依赖和网络连接") from e
            
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def _fetch_from_akshare(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """带重试机制的AkShare数据获取"""
        try:
            df = ak.stock_zh_a_daily(
                symbol=symbol, 
                start_date=start_date,
                end_date=end_date,
                adjust="hfq"
            )
            return df
        except Exception as e:
            logger.error(f"AkShare请求失败: {str(e)}")
            raise
            
    def _convert_data_format(self, raw_df: pd.DataFrame) -> pd.DataFrame:
        """将AkShare数据格式转换为项目标准格式"""
        df = raw_df.copy()
        
        # 字段重命名
        df.rename(columns=self._field_mapping, inplace=True)
        
        # 日期格式标准化
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date']).dt.strftime('%Y%m%d')
            df.set_index('date', inplace=True)
            
        # 类型转换
        numeric_cols = ['open', 'close', 'high', 'low', 'volume', 'amount']
        df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors='coerce')
        
        return df

    @lru_cache(maxsize=128)
    def get_data(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """获取股票历史数据"""
        if not self._initialized:
            raise RuntimeError("AkShare数据源未初始化")
            
        try:
            raw_df = self._fetch_from_akshare(symbol, start_date, end_date)
            processed_df = self._convert_data_format(raw_df)
            return processed_df
        except Exception as e:
            logger.error(f"获取数据失败: {symbol} {start_date}-{end_date}")
            raise RuntimeError(f"数据获取失败: {str(e)}") from e
            
    def clear_cache(self):
        """清理缓存"""
        self.get_data.cache_clear()
        logger.info("AkShare数据缓存已清除")

    @property
    def available_symbols(self) -> list:
        """获取可用的股票代码列表"""
        try:
            spot_df = ak.stock_zh_a_spot()
            return spot_df['代码'].tolist()
        except Exception as e:
            logger.error("获取股票列表失败")
            return []

    # @st.cache_data
    def get_market_fund_flow(self) -> pd.DataFrame:
        """获取大盘资金流向数据"""
        try:
            df = ak.stock_market_fund_flow()
            # print(df.columns)
            # print(df.shape)
            
            # 字段重命名
            df.rename(columns={
                '日期': 'date',
                '上证-收盘价': 'sh_close',          # 上海市场收盘价
                '上证-涨跌幅': 'sh_change_pct',     # 上海市场涨跌幅百分比
                '深证-收盘价': 'sz_close',          # 深圳市场收盘价
                '深证-涨跌幅': 'sz_change_pct',     # 深圳市场涨跌幅百分比
                '主力净流入-净额': 'main_net_inflow_amt',       # 主力资金净流入金额
                '主力净流入-净占比': 'main_net_inflow_ratio',    # 主力资金净流入占比
                '超大单净流入-净额': 'super_large_net_inflow_amt',  # 超大单资金净流入金额
                '超大单净流入-净占比': 'super_large_net_inflow_ratio', # 超大单资金净流入占比
                '大单净流入-净额': 'large_net_inflow_amt',       # 大单资金净流入金额
                '大单净流入-净占比': 'large_net_inflow_ratio',    # 大单资金净流入占比
                '中单净流入-净额': 'mid_net_inflow_amt',        # 中单资金净流入金额
                '中单净流入-净占比': 'mid_net_inflow_ratio',     # 中单资金净流入占比
                '小单净流入-净额': 'retail_net_inflow_amt',      # 散户资金净流入金额
                '小单净流入-净占比': 'retail_net_inflow_ratio'   # 散户资金净流入占比
            }, inplace=True)

            # 日期格式调整
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values(by = 'date',ascending=True)
            
            return df
        except Exception as e:
            logger.error("获取大盘资金流向失败")
            raise RuntimeError(f"获取大盘资金流向失败: {str(e)}") from e
