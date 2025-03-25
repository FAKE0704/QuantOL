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
        """智能加载数据，优先从数据库获取，不存在则从API获取"""
        freq = frequency if frequency is not None else self.default_frequency
        cache_key = f"{symbol}_{freq}_{start_date}_{end_date}"
        
        # 首先尝试从数据库获取数据
        db_manager = DatabaseManager()
        db_data = db_manager.load_stock_data(symbol, start_date, end_date, freq)
        
        # 如果数据库中存在完整数据，直接返回
        if not db_data.empty:
            self.cache[cache_key] = db_data
            return db_data
            
        # 如果数据库中没有数据，则从API获取
        api_frequency = freq
        
        # 检查内存缓存
        if cache_key in self.cache:
            return self.cache[cache_key]
            
        # 检查磁盘缓存
        if self.cache_dir:
            cache_file = os.path.join(self.cache_dir, f"{cache_key}.parquet")
            if os.path.exists(cache_file):
                df = pd.read_parquet(cache_file)
                self.cache[cache_key] = df
                # 将缓存数据保存到数据库
                db_manager.save_stock_data(df, symbol, freq)
                return df

        # 从API获取数据
        lg = bs.login()
        
        if api_frequency in ["1", "5", "15", "30", "60"]:
            fields = "date,time,code,open,high,low,close,volume,amount,adjustflag"
        else:
            fields = "date,code,open,high,low,close,preclose,volume,amount,adjustflag,turn,tradestatus,pctChg,isST"
            
        rs = bs.query_history_k_data_plus(
            symbol,
            fields,
            start_date=start_date,
            end_date=end_date,
            frequency=api_frequency,
            adjustflag="3"
        )
        
        data_list = []
        while (rs.error_code == "0") & rs.next():
            data_list.append(rs.get_row_data())
        
        bs.logout()
        
        if not data_list:
            raise DataSourceError(f"未获取到数据, symbol: {symbol}, frequency: {api_frequency}")
            
        # 将获取到的数据保存到数据库
        db_manager.save_stock_data(df, symbol, freq)
            
        df = pd.DataFrame(data_list, columns=rs.fields)
        df = self._transform_data(df)
        
        # 缓存数据
        self.cache[cache_key] = df
        if self.cache_dir:
            df.to_parquet(cache_file)
            
        return df

    def check_data_exists(self, symbol: str, frequency: Optional[str] = None) -> bool:
        """检查指定股票和频率的数据是否存在"""
        if not self.cache_dir:
            return False
            
        freq = frequency if frequency is not None else self.default_frequency
        cache_file = os.path.join(self.cache_dir, f"{symbol}_{freq}.parquet")
        return os.path.exists(cache_file)

    def save_data(self, data: pd.DataFrame, symbol: str, frequency: str) -> bool:
        """保存数据到本地缓存"""
        if not self.cache_dir:
            return False
            
        try:
            cache_file = os.path.join(self.cache_dir, f"{symbol}_{frequency}.parquet")
            data.to_parquet(cache_file)
            return True
        except Exception as e:
            print(f"保存数据失败: {str(e)}")
            return False

    def _transform_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """标准化数据格式"""
        if 'date' in data.columns:
            data['date'] = pd.to_datetime(data['date'])
        if 'time' in data.columns:
            # 截取前14位字符并转换为datetime
            data['time'] = pd.to_datetime(
                data['time'].str[:14], 
                format="%Y%m%d%H%M%S"
            )
            
        data = data.rename(columns={
            'open': 'Open',
            'high': 'High',
            'low': 'Low',
            'close': 'Close',
            'volume': 'Volume'
        })
        
        return data[['date', 'Open', 'High', 'Low', 'Close', 'Volume']]
