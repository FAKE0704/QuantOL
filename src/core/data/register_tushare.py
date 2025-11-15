"""
注册Tushare数据源到DataFactory
这个文件负责将新的tushare服务适配器注册到数据源工厂中
"""

from .data_factory import DataFactory
from .adapters.tushare_service_adapter import TushareServiceAdapter


def register_tushare_source():
    """
    注册Tushare数据源到工厂
    """
    DataFactory.register_source("tushare", TushareServiceAdapter)


def get_tushare_source(**kwargs):
    """
    获取Tushare数据源实例

    Args:
        **kwargs: 传递给TushareServiceAdapter的参数

    Returns:
        TushareServiceAdapter实例
    """
    return DataFactory.get_source("tushare", **kwargs)


# 自动注册
register_tushare_source()


# 导出的便捷函数
__all__ = [
    'register_tushare_source',
    'get_tushare_source',
    'TushareServiceAdapter'
]