"""
智能数据管理器
统一的智能数据获取接口，自动选择最佳数据源
"""

import asyncio
import logging
from typing import Dict, List, Optional, Union, Any
import pandas as pd
from datetime import datetime, date
from enum import Enum

from .data_source_selector import DataSourceSelector, DataSourceRequest, get_data_source_selector
from .config.data_source_config import get_data_source_manager, DataSourceType


class DataType(Enum):
    """数据类型枚举"""
    STOCK_BASIC = "stock_basic"      # 股票基本信息
    MARKET_DATA = "market_data"      # 市场数据（日线、周线等）
    REALTIME_QUOTE = "realtime"      # 实时行情
    FINANCIAL_DATA = "financial"     # 财务数据
    INDEX_DATA = "index_data"        # 指数数据
    MACRO_DATA = "macro_data"        # 宏观数据


class SmartDataManager:
    """
    智能数据管理器
    提供统一的数据获取接口，自动处理数据源选择、降级和错误重试
    """

    def __init__(self, selector: Optional[DataSourceSelector] = None):
        self.selector = selector or get_data_source_selector()
        self.logger = logging.getLogger(__name__)

    # ==================== 股票基本信息 ====================

    async def get_stock_list(self, exchange: str = '', list_status: str = 'L',
                           use_fallback: bool = True) -> pd.DataFrame:
        """
        获取股票列表

        Args:
            exchange: 交易所代码
            list_status: 上市状态
            use_fallback: 是否使用备用数据源

        Returns:
            股票列表DataFrame
        """
        request = DataSourceRequest(
            request_type=DataType.STOCK_BASIC.value,
            fallback_enabled=use_fallback,
            timeout=30.0
        )

        try:
            return await self.selector.execute_with_fallback(
                request, 'get_stock_list', exchange, list_status
            )
        except Exception as e:
            self.logger.error(f"获取股票列表失败: {e}")
            raise

    async def get_stock_info(self, symbol: str, use_fallback: bool = True) -> Dict[str, Any]:
        """
        获取单个股票的基本信息

        Args:
            symbol: 股票代码
            use_fallback: 是否使用备用数据源

        Returns:
            股票基本信息字典
        """
        try:
            stock_list = await self.get_stock_list(use_fallback=use_fallback)
            stock_info = stock_list[stock_list['symbol_code'] == symbol]

            if not stock_info.empty:
                return stock_info.iloc[0].to_dict()
            else:
                raise ValueError(f"未找到股票 {symbol} 的信息")

        except Exception as e:
            self.logger.error(f"获取股票信息失败: {e}")
            raise

    async def search_stocks(self, keyword: str, search_fields: List[str] = None,
                           use_fallback: bool = True) -> pd.DataFrame:
        """
        搜索股票

        Args:
            keyword: 搜索关键词
            search_fields: 搜索字段列表
            use_fallback: 是否使用备用数据源

        Returns:
            搜索结果DataFrame
        """
        try:
            stock_list = await self.get_stock_list(use_fallback=use_fallback)
            if stock_list.empty:
                return pd.DataFrame()

            # 默认搜索字段
            if search_fields is None:
                search_fields = ['name', 'symbol_code', 'industry', 'area']

            # 执行搜索
            mask = pd.Series([False] * len(stock_list))
            for field in search_fields:
                if field in stock_list.columns:
                    mask |= stock_list[field].astype(str).str.contains(keyword, case=False, na=False)

            return stock_list[mask]

        except Exception as e:
            self.logger.error(f"搜索股票失败: {e}")
            raise

    # ==================== 市场数据 ====================

    async def get_market_data(self, symbol: str, start_date: str, end_date: str,
                            frequency: str = 'D', use_fallback: bool = True) -> pd.DataFrame:
        """
        获取市场数据（日线、周线等）

        Args:
            symbol: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            frequency: 数据频率（D日线，W周线，M月线）
            use_fallback: 是否使用备用数据源

        Returns:
            市场数据DataFrame
        """
        request = DataSourceRequest(
            request_type=DataType.MARKET_DATA.value,
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            frequency=frequency,
            fallback_enabled=use_fallback,
            timeout=60.0
        )

        try:
            return await self.selector.execute_with_fallback(
                request, 'load_data', symbol, start_date, end_date, frequency
            )
        except Exception as e:
            self.logger.error(f"获取市场数据失败: {e}")
            raise

    async def get_multiple_stocks_data(self, symbols: List[str], start_date: str, end_date: str,
                                     frequency: str = 'D', use_fallback: bool = True) -> Dict[str, pd.DataFrame]:
        """
        批量获取多个股票的市场数据

        Args:
            symbols: 股票代码列表
            start_date: 开始日期
            end_date: 结束日期
            frequency: 数据频率
            use_fallback: 是否使用备用数据源

        Returns:
            股票代码到数据的映射字典
        """
        results = {}

        # 尝试使用支持批量操作的数据源
        try:
            request = DataSourceRequest(
                request_type=DataType.MARKET_DATA.value,
                fallback_enabled=use_fallback,
                timeout=120.0
            )

            # 检查是否有支持批量操作的数据源
            enabled_sources = self.selector.config_manager.get_data_sources_by_priority()
            tushare_sources = [s for s in enabled_sources if s.source_type == DataSourceType.TUSHARE]

            if tushare_sources and use_fallback:
                # 使用Tushare的批量接口
                tushare_config = tushare_sources[0]
                tushare_instance = await self.selector.get_data_source_instance(tushare_config.name)
                if hasattr(tushare_instance, 'service'):
                    results = await tushare_instance.service.batch_get_market_data(
                        symbols, start_date, end_date, frequency, use_fallback
                    )
                    return results

        except Exception as e:
            self.logger.warning(f"批量获取失败，转为逐个获取: {e}")

        # 逐个获取数据
        for symbol in symbols:
            try:
                data = await self.get_market_data(
                    symbol, start_date, end_date, frequency, use_fallback
                )
                results[symbol] = data
            except Exception as e:
                self.logger.error(f"获取 {symbol} 数据失败: {e}")
                results[symbol] = pd.DataFrame()  # 返回空DataFrame

        return results

    # ==================== 实时行情 ====================

    async def get_realtime_quotes(self, symbols: List[str], use_fallback: bool = True) -> pd.DataFrame:
        """
        获取实时行情

        Args:
            symbols: 股票代码列表
            use_fallback: 是否使用备用数据源

        Returns:
            实时行情DataFrame
        """
        request = DataSourceRequest(
            request_type=DataType.REALTIME_QUOTE.value,
            fallback_enabled=use_fallback,
            timeout=30.0
        )

        try:
            return await self.selector.execute_with_fallback(
                request, 'get_realtime_quotes', symbols
            )
        except Exception as e:
            self.logger.error(f"获取实时行情失败: {e}")
            raise

    async def get_single_realtime_quote(self, symbol: str, use_fallback: bool = True) -> Dict[str, Any]:
        """
        获取单个股票的实时行情

        Args:
            symbol: 股票代码
            use_fallback: 是否使用备用数据源

        Returns:
            实时行情字典
        """
        try:
            quotes = await self.get_realtime_quotes([symbol], use_fallback=use_fallback)
            if not quotes.empty:
                return quotes.iloc[0].to_dict()
            else:
                raise ValueError(f"未找到股票 {symbol} 的实时行情")

        except Exception as e:
            self.logger.error(f"获取实时行情失败: {e}")
            raise

    # ==================== 财务数据 ====================

    async def get_financial_data(self, symbol: str, start_date: str, end_date: str,
                               report_type: str = '1', use_fallback: bool = True) -> pd.DataFrame:
        """
        获取财务数据

        Args:
            symbol: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            report_type: 报告类型
            use_fallback: 是否使用备用数据源

        Returns:
            财务数据DataFrame
        """
        request = DataSourceRequest(
            request_type=DataType.FINANCIAL_DATA.value,
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            fallback_enabled=use_fallback,
            timeout=60.0
        )

        try:
            return await self.selector.execute_with_fallback(
                request, 'get_financial_data', symbol, start_date, end_date, report_type
            )
        except Exception as e:
            self.logger.error(f"获取财务数据失败: {e}")
            raise

    async def get_latest_financial_data(self, symbol: str, use_fallback: bool = True) -> pd.DataFrame:
        """
        获取最新财务数据

        Args:
            symbol: 股票代码
            use_fallback: 是否使用备用数据源

        Returns:
            最新财务数据DataFrame
        """
        # 设置时间范围为最近两年的财务数据
        end_date = datetime.now().strftime('%Y%m%d')
        start_date = (datetime.now().replace(year=datetime.now().year - 2)).strftime('%Y%m%d')

        return await self.get_financial_data(symbol, start_date, end_date, use_fallback=use_fallback)

    # ==================== 指数数据 ====================

    async def get_index_list(self, exchange: str = '', market: str = '',
                           use_fallback: bool = True) -> pd.DataFrame:
        """
        获取指数列表

        Args:
            exchange: 交易所代码
            market: 市场代码
            use_fallback: 是否使用备用数据源

        Returns:
            指数列表DataFrame
        """
        request = DataSourceRequest(
            request_type=DataType.INDEX_DATA.value,
            fallback_enabled=use_fallback,
            timeout=30.0
        )

        try:
            return await self.selector.execute_with_fallback(
                request, 'get_index_list', exchange, market
            )
        except Exception as e:
            self.logger.error(f"获取指数列表失败: {e}")
            raise

    async def get_index_data(self, symbol: str, start_date: str, end_date: str,
                           use_fallback: bool = True) -> pd.DataFrame:
        """
        获取指数数据

        Args:
            symbol: 指数代码
            start_date: 开始日期
            end_date: 结束日期
            use_fallback: 是否使用备用数据源

        Returns:
            指数数据DataFrame
        """
        request = DataSourceRequest(
            request_type=DataType.INDEX_DATA.value,
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            fallback_enabled=use_fallback,
            timeout=60.0
        )

        try:
            return await self.selector.execute_with_fallback(
                request, 'load_data', symbol, start_date, end_date, 'D'
            )
        except Exception as e:
            self.logger.error(f"获取指数数据失败: {e}")
            raise

    # ==================== 智能数据获取 ====================

    async def get_data_smart(self, symbol: str, data_type: DataType,
                           start_date: str = None, end_date: str = None,
                           frequency: str = 'D', **kwargs) -> pd.DataFrame:
        """
        智能数据获取，根据数据类型自动选择合适的方法

        Args:
            symbol: 股票/指数代码
            data_type: 数据类型
            start_date: 开始日期
            end_date: 结束日期
            frequency: 数据频率
            **kwargs: 其他参数

        Returns:
            数据DataFrame
        """
        try:
            if data_type == DataType.STOCK_BASIC:
                if symbol:
                    # 获取单个股票信息
                    info = await self.get_stock_info(symbol)
                    return pd.DataFrame([info])
                else:
                    # 获取股票列表
                    return await self.get_stock_list(**kwargs)

            elif data_type == DataType.MARKET_DATA:
                if not start_date or not end_date:
                    raise ValueError("市场数据需要指定开始和结束日期")
                return await self.get_market_data(symbol, start_date, end_date, frequency)

            elif data_type == DataType.REALTIME_QUOTE:
                if isinstance(symbol, str):
                    # 单个股票
                    info = await self.get_single_realtime_quote(symbol)
                    return pd.DataFrame([info])
                else:
                    # 多个股票
                    return await self.get_realtime_quotes(symbol)

            elif data_type == DataType.FINANCIAL_DATA:
                if not start_date or not end_date:
                    return await self.get_latest_financial_data(symbol)
                else:
                    return await self.get_financial_data(symbol, start_date, end_date, **kwargs)

            elif data_type == DataType.INDEX_DATA:
                if symbol:
                    return await self.get_index_data(symbol, start_date, end_date)
                else:
                    return await self.get_index_list(**kwargs)

            else:
                raise ValueError(f"不支持的数据类型: {data_type}")

        except Exception as e:
            self.logger.error(f"智能数据获取失败: {e}")
            raise

    # ==================== 系统管理 ====================

    async def test_all_connections(self) -> Dict[str, Any]:
        """测试所有数据源连接"""
        try:
            await self.selector.refresh_all_source_status()
            source_status = self.selector.get_all_source_status()

            results = {}
            for name, status in source_status.items():
                results[name] = {
                    'available': status.is_available,
                    'last_check': status.last_check_time,
                    'response_time': status.response_time,
                    'error_message': status.error_message
                }

            return results

        except Exception as e:
            self.logger.error(f"测试连接失败: {e}")
            return {}

    def get_system_stats(self) -> Dict[str, Any]:
        """获取系统统计信息"""
        try:
            stats = self.selector.get_request_stats()
            config_summary = self.selector.config_manager.get_config_summary()

            return {
                'request_stats': stats,
                'config_summary': config_summary,
                'supported_sources': [stype.value for stype in self.selector.config_manager.supported_sources.keys()]
            }

        except Exception as e:
            self.logger.error(f"获取系统统计失败: {e}")
            return {}

    async def health_check(self) -> Dict[str, Any]:
        """执行系统健康检查"""
        try:
            # 测试连接
            connection_results = await self.test_all_connections()

            # 检查配置
            config_summary = self.selector.config_manager.get_config_summary()

            # 统计分析
            stats = self.selector.get_request_stats()

            # 计算健康分数
            healthy_sources = sum(1 for r in connection_results.values() if r['available'])
            total_enabled_sources = config_summary['enabled_sources']
            health_score = (healthy_sources / total_enabled_sources * 100) if total_enabled_sources > 0 else 0

            # 生成健康状态
            if health_score >= 80:
                health_status = "healthy"
            elif health_score >= 60:
                health_status = "warning"
            else:
                health_status = "critical"

            return {
                'status': health_status,
                'health_score': health_score,
                'healthy_sources': healthy_sources,
                'total_enabled_sources': total_enabled_sources,
                'connection_results': connection_results,
                'config_summary': config_summary,
                'request_stats': stats,
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            self.logger.error(f"健康检查失败: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }


# 全局智能数据管理器实例
_global_manager: Optional[SmartDataManager] = None


def get_smart_data_manager() -> SmartDataManager:
    """获取全局智能数据管理器实例"""
    global _global_manager
    if _global_manager is None:
        _global_manager = SmartDataManager()
    return _global_manager


def init_smart_data_manager(selector: Optional[DataSourceSelector] = None) -> SmartDataManager:
    """初始化全局智能数据管理器"""
    global _global_manager
    _global_manager = SmartDataManager(selector)
    return _global_manager


# ==================== 便捷函数 ====================

async def get_stock_list(exchange: str = '', list_status: str = 'L') -> pd.DataFrame:
    """便捷函数：获取股票列表"""
    manager = get_smart_data_manager()
    return await manager.get_stock_list(exchange, list_status)


async def get_stock_data(symbol: str, start_date: str, end_date: str, frequency: str = 'D') -> pd.DataFrame:
    """便捷函数：获取股票数据"""
    manager = get_smart_data_manager()
    return await manager.get_market_data(symbol, start_date, end_date, frequency)


async def get_realtime_data(symbols: List[str]) -> pd.DataFrame:
    """便捷函数：获取实时数据"""
    manager = get_smart_data_manager()
    return await manager.get_realtime_quotes(symbols)


def get_stock_data_sync(symbol: str, start_date: str, end_date: str, frequency: str = 'D') -> pd.DataFrame:
    """便捷函数：同步获取股票数据（兼容旧接口）"""
    return asyncio.run(get_stock_data(symbol, start_date, end_date, frequency))