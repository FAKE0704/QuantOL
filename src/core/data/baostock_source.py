import pandas as pd
import baostock as bs
from .data_source import DataSource, DataSourceError
from .data_factory import DataFactory
from typing import Optional
from datetime import date, datetime, timedelta
from core.data.database import DatabaseManager
import os
from datetime import datetime

class BaostockDataSource(DataSource):
    """Baostock数据源实现"""
    
    def __init__(self, frequency: str = "5", cache_dir: Optional[str] = None):
        super().__init__()
        self.cache_dir = cache_dir
        self.cache: dict = {}
        self.default_frequency = frequency
        
        # 创建缓存目录
        if cache_dir and not os.path.exists(cache_dir):
            os.makedirs(cache_dir)

    async def load_data(self, symbol: str, start_date: date, end_date: date, frequency: Optional[str] = None) -> pd.DataFrame:
        """从baostock获取股票symbol从start_date到end_date的频率frequency数据
        Args:
            symbol: 股票代码
            start_date: 开始日期(date对象)
            end_date: 结束日期(date对象)
            frequency: 数据频率(可选)
        """
        # 处理单日查询情况
        if start_date == end_date:
            start_date = end_date - timedelta(days=1)
            
            
        # 转换为baostock需要的日期格式
        start_date_str = start_date.strftime("%Y-%m-%d")
        end_date_str = end_date.strftime("%Y-%m-%d")

        from services.progress_service import progress_service
        
        freq = frequency if frequency is not None else self.default_frequency
        task_id = f"{symbol}_{freq}_load"
        progress_service.start_task(task_id, 1)
        
        lg = bs.login()
        if lg.error_code != '0':
            progress_service.end_task(task_id)
            raise DataSourceError(f"Baostock登录失败: {lg.error_msg}")
        
        if freq in ["1", "5", "15", "30", "60"]:
            fields = "date,time,code,open,high,low,close,volume,amount,adjustflag"
        else:
            fields = "date,code,open,high,low,close,preclose,volume,amount,adjustflag,turn,tradestatus,pctChg,isST"
        
        
        rs = bs.query_history_k_data_plus(
            symbol,
            fields,
            start_date=start_date_str,
            end_date=end_date_str,
            frequency=freq,
            adjustflag="3"
        ) # 日期格式需要为 20250202
        

        if rs.error_code != '0':
            bs.logout()
            progress_service.end_task(task_id)
            raise DataSourceError(f"获取历史数据失败: {rs.error_msg}")
        
        data_list = []
        total = len(rs.get_row_data())
        processed = 0
        while rs.next():
            data_list.append(rs.get_row_data())
            processed += 1
            progress_service.update_progress(task_id, processed / total)
        
        bs.logout()
        progress_service.end_task(task_id)
        
        if not data_list:
            raise DataSourceError(
                f"未获取到数据, symbol: {symbol}, "
                f"start_date:{start_date_str}, "
                f"end_date:{end_date_str}, "
                f"frequency: {freq}"
            )
            
        df = pd.DataFrame(data_list, columns=rs.fields)
        
        # 将获取到的数据_时间数据标准化
        df = self._transform_data(df)
            
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
                data['time'].str[8:13], 
                format="%H%M%S"
            )
        
        # Convert numpy datetime64 to Python datetime
        data['date'] = data['date'].dt.strftime('%Y-%m-%d')
        if 'time' in data.columns:
            data['time'] = data['time'].dt.time

        return data

    async def _get_all_stocks(self) -> pd.DataFrame:
        """从Baostock获取所有股票信息"""
        from services.progress_service import progress_service
        
        task_id = "stock_list_load"
        progress_service.start_task(task_id, 1)  # 初始化进度任务
        
        try:
            # 登录Baostock
            lg = bs.login()
            if lg.error_code != '0':
                raise ConnectionError(f"Baostock登录失败: {lg.error_msg}")

            # 获取证券基本资料
            rs = bs.query_stock_basic()
            if rs.error_code != '0':
                raise RuntimeError(f"获取所有股票信息失败: {rs.error_msg}")

            data_list = []
            total = len(rs.data)
            processed = 0
            
            # 处理数据并更新进度
            while rs.next():
                data_list.append(rs.get_row_data())
                processed += 1
                progress_service.update_progress(
                    task_id, 
                    min(processed / total, 0.99)  # 保留1%用于最后的登出操作
                )
            
            return pd.DataFrame(data_list, columns=rs.fields)
            
        except Exception as e:
            progress_service.update_progress(task_id, 1.0)
            print(f"股票数据获取失败: {str(e)}")
            raise
        finally:
            bs.logout()
            progress_service.end_task(task_id)

    async def get_money_supply_data(self, start_date: str, end_date: str) -> pd.DataFrame:
        """获取货币供应量数据并保存到数据库
        
        Args:
            start_date: 开始日期 (格式: YYYY-MM)
            end_date: 结束日期 (格式: YYYY-MM)
            
        Returns:
            包含货币供应量数据的DataFrame
        """
        from services.progress_service import progress_service
        
        task_id = "money_supply_load"
        progress_service.start_task(task_id, 1)
        
        try:
            # 登录Baostock
            lg = bs.login()
            if lg.error_code != '0':
                progress_service.end_task(task_id)
                raise DataSourceError(f"Baostock登录失败: {lg.error_msg}")
            
            # 获取货币供应量数据
            rs = bs.query_money_supply_data_month(start_date=start_date, end_date=end_date)
            if rs.error_code != '0':
                bs.logout()
                progress_service.end_task(task_id)
                raise DataSourceError(f"获取货币供应量失败: {rs.error_msg}")
            
            # 处理数据
            data_list = []
            while (rs.error_code == '0') & rs.next():
                data_list.append(rs.get_row_data())
            
            if not data_list:
                bs.logout()
                progress_service.end_task(task_id)
                raise DataSourceError("未获取到货币供应量数据")
                
            df = pd.DataFrame(data_list, columns=rs.fields)
            
            # 转换字段名格式
            df.rename(columns={
                'statMonth': 'stat_month',
                'm2YoY': 'm2_yoy',
                'm1YoY': 'm1_yoy',
                'm0YoY': 'm0_yoy',
                'cdYoY': 'cd_yoy',
                'qmYoY': 'qm_yoy',
                'ftdYoY': 'ftd_yoy',
                'sdYoY': 'sd_yoy'
            }, inplace=True)
            
            # 保存到数据库
            db = DatabaseManager()
            await db.save_money_supply_data(df)
            
            bs.logout()
            progress_service.end_task(task_id)
            return df
            
        except Exception as e:
            progress_service.end_task(task_id)
            raise DataSourceError(f"获取货币供应量数据失败: {str(e)}")

# 注册到数据源工厂
DataFactory.register_source("baostock", BaostockDataSource)
