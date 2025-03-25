import pandas as pd
import baostock as bs
from .data_source import DataSource, DataSourceError
from typing import Optional
import os

class BaostockDataSource(DataSource):
    """Baostock数据源实现"""
    
    def __init__(self, frequency: str, cache_dir: Optional[str] = None):
        super().__init__()
        self.cache_dir = cache_dir
        self.cache: dict = {}
        self.default_frequency = frequency
        
        # 创建缓存目录
        if cache_dir and not os.path.exists(cache_dir):
            os.makedirs(cache_dir)

    async def load_data(self, symbol: str, start_date: str, end_date: str, frequency: Optional[str] = None) -> pd.DataFrame:
        """异步加载数据"""
        # 使用传入的frequency，如果未传入则使用默认值
        freq = frequency if frequency is not None else self.default_frequency
        cache_key = f"{symbol}_{freq}_{start_date}_{end_date}"
        
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

        # 使用baostock获取数据
        lg = bs.login()
        
        if frequency in ["1", "5", "15", "30", "60"]:
            fields = "date,time,code,open,high,low,close,volume,amount,adjustflag"
        else:
            fields = "date,code,open,high,low,close,preclose,volume,amount,adjustflag,turn,tradestatus,pctChg,isST"
            
        rs = bs.query_history_k_data_plus(
            symbol,
            fields,
            start_date=start_date,
            end_date=end_date,
            frequency=frequency,
            adjustflag="3"
        )
        
        data_list = []
        while (rs.error_code == "0") & rs.next():
            data_list.append(rs.get_row_data())
        
        bs.logout()
        
        if not data_list:
            raise DataSourceError(f"未获取到数据, symbol: {symbol}, frequency: {frequency}")
            
        df = pd.DataFrame(data_list, columns=rs.fields)
        df = self._transform_data(df)
        
        # 缓存数据
        self.cache[cache_key] = df
        if self.cache_dir:
            df.to_parquet(cache_file)
            
        return df

    def _transform_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """标准化数据格式"""
        if 'date' in data.columns:
            data['date'] = pd.to_datetime(data['date'])
        if 'time' in data.columns:
            data['time'] = pd.to_datetime(data['time'], format="%Y%m%d%H%M")
            
        data = data.rename(columns={
            'open': 'Open',
            'high': 'High',
            'low': 'Low',
            'close': 'Close',
            'volume': 'Volume'
        })
        
        return data[['date', 'Open', 'High', 'Low', 'Close', 'Volume']]
