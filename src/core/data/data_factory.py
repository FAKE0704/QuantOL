import threading
import pandas as pd
from typing import Dict, Type, Optional
from .data_source import DataSource

class DataFactory(DataSource):
    """数据源工厂类，实现单例模式和线程安全的数据源管理"""
    
    _instance = None
    _lock = threading.Lock()
    _source_lock = threading.Lock()
    _registered_sources: Dict[str, Type[DataSource]] = {}
    
    def __new__(cls):
        """实现单例模式"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    def register_source(cls, name: str, source_class: Type[DataSource]) -> None:
        """注册数据源类型"""
        with cls._source_lock:
            cls._registered_sources[name] = source_class
    
    @classmethod
    def get_source(cls, name: str, *args, **kwargs) -> Optional[DataSource]:
        """获取数据源实例"""
        with cls._source_lock:
            source_class = cls._registered_sources.get(name)
            if source_class:
                return source_class(*args, **kwargs)
        return None
    
    async def load_data(self, symbol: str, start_date: str, end_date: str, frequency: str) -> pd.DataFrame:
        """加载数据（需由具体数据源实现）"""
        raise NotImplementedError("Should be implemented by concrete data source")
    
    def save_data(self, data: pd.DataFrame, symbol: str, frequency: str) -> bool:
        """保存数据（需由具体数据源实现）"""
        raise NotImplementedError("Should be implemented by concrete data source")
    
    def check_data_exists(self, symbol: str, frequency: str) -> bool:
        """检查数据是否存在（需由具体数据源实现）"""
        raise NotImplementedError("Should be implemented by concrete data source")