"""
数据源模块初始化
"""

# 导入基础数据源接口
from .data_source import DataSource
from .akshare_source import AkShareSource
from .baostock_source import BaostockDataSource
from .data_factory import DataFactory

# 导入新的tushare数据源组件
from .adapters.tushare_adapter import TushareAdapter
from .adapters.tushare_service_adapter import TushareServiceAdapter
from .transformers.data_transformer import DataTransformer
from .cache.cache_manager import CacheManager
from .config.tushare_config import TushareConfig, init_global_config_from_env

# 导入tushare注册模块（会自动注册到DataFactory）
from .register_tushare import register_tushare_source, get_tushare_source

__all__ = [
    # 基础组件
    'DataSource',
    'DataFactory',
    'AkShareSource',
    'BaostockDataSource',

    # 新的tushare组件
    'TushareAdapter',
    'TushareServiceAdapter',
    'DataTransformer',
    'CacheManager',
    'TushareConfig',

    # 注册函数
    'register_tushare_source',
    'get_tushare_source',
    'init_global_config_from_env'
]
