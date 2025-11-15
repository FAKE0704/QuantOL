"""
数据源选择器
根据用户配置和优先级智能选择数据源
"""

import asyncio
import logging
from typing import Dict, List, Optional, Union, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass

from .data_factory import DataFactory
from .config.data_source_config import (
    DataSourceManager, DataSourceConfig, DataSourceType, DataSourcePriority,
    get_data_source_manager
)
from .data_source import DataSource


@dataclass
class DataSourceStatus:
    """数据源状态"""
    name: str
    is_available: bool
    last_check_time: Optional[datetime]
    error_message: Optional[str]
    response_time: Optional[float]
    success_rate: float
    last_success_time: Optional[datetime]


@dataclass
class DataSourceRequest:
    """数据源请求上下文"""
    request_type: str  # 'stock_basic', 'market_data', 'realtime', etc.
    symbol: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    frequency: Optional[str] = None
    priority_override: Optional[DataSourcePriority] = None
    fallback_enabled: bool = True
    timeout: float = 30.0


class DataSourceSelector:
    """数据源选择器"""

    def __init__(self, config_manager: Optional[DataSourceManager] = None):
        self.config_manager = config_manager or get_data_source_manager()
        self.logger = logging.getLogger(__name__)

        # 数据源状态跟踪
        self.source_status: Dict[str, DataSourceStatus] = {}

        # 请求统计
        self.request_stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'fallback_used': 0
        }

        # 初始化数据源状态
        self._initialize_source_status()

    def _initialize_source_status(self):
        """初始化数据源状态"""
        for name, config in self.config_manager.get_all_data_sources().items():
            self.source_status[name] = DataSourceStatus(
                name=name,
                is_available=None,  # 未知状态，需要检测
                last_check_time=None,
                error_message=None,
                response_time=None,
                success_rate=0.0,
                last_success_time=None
            )

    async def select_best_source(self, request: DataSourceRequest) -> Optional[str]:
        """
        根据请求和配置选择最佳数据源

        Args:
            request: 数据源请求上下文

        Returns:
            选择的数据源名称，如果没有可用的数据源则返回None
        """
        self.request_stats['total_requests'] += 1

        try:
            # 获取按优先级排序的启用数据源
            enabled_sources = self.config_manager.get_data_sources_by_priority()

            if not enabled_sources:
                self.logger.warning("没有启用的数据源")
                return None

            # 根据请求类型过滤支持的数据源
            suitable_sources = await self._filter_suitable_sources(enabled_sources, request)

            if not suitable_sources:
                self.logger.warning(f"没有支持请求类型 {request.request_type} 的数据源")
                return None

            # 检查数据源可用性并选择最佳源
            best_source = await self._select_best_available_source(suitable_sources, request)

            if best_source:
                self.logger.info(f"选择数据源: {best_source.name} for {request.request_type}")
                return best_source.name
            else:
                self.logger.warning("没有可用的数据源")
                return None

        except Exception as e:
            self.logger.error(f"选择数据源失败: {e}")
            self.request_stats['failed_requests'] += 1
            return None

    async def _filter_suitable_sources(self, sources: List[DataSourceConfig],
                                     request: DataSourceRequest) -> List[DataSourceConfig]:
        """
        根据请求类型过滤支持的数据源

        Args:
            sources: 数据源配置列表
            request: 请求上下文

        Returns:
            支持当前请求类型的数据源列表
        """
        suitable_sources = []

        # 定义各数据源支持的请求类型
        source_capabilities = {
            DataSourceType.TUSHARE: {
                'stock_basic', 'market_data', 'realtime', 'financial_data', 'index_data'
            },
            DataSourceType.BAOSTOCK: {
                'stock_basic', 'market_data'
            },
            DataSourceType.YAHOO: {
                'stock_basic', 'market_data', 'realtime'
            },
            DataSourceType.AKSHARE: {
                'stock_basic', 'market_data', 'financial_data', 'index_data'
            }
        }

        for source in sources:
            capabilities = source_capabilities.get(source.source_type, set())

            if request.request_type in capabilities:
                suitable_sources.append(source)
            else:
                self.logger.debug(f"数据源 {source.name} 不支持请求类型 {request.request_type}")

        return suitable_sources

    async def _select_best_available_source(self, sources: List[DataSourceConfig],
                                          request: DataSourceRequest) -> Optional[DataSourceConfig]:
        """
        从合适的数据源中选择最佳可用源

        Args:
            sources: 合适的数据源列表
            request: 请求上下文

        Returns:
            最佳数据源配置，如果没有可用的则返回None
        """
        available_sources = []

        for source in sources:
            status = self.source_status.get(source.name)

            # 检查数据源是否可用
            is_available = await self._check_source_availability(source, status)

            if is_available:
                available_sources.append((source, status))
            elif request.fallback_enabled:
                self.logger.debug(f"数据源 {source.name} 不可用，尝试下一个")

        if not available_sources:
            return None

        # 按优先级和状态排序选择最佳源
        # 优先级顺序：用户指定的优先级 > 可用性 > 响应时间 > 成功率
        best_source, best_status = min(
            available_sources,
            key=lambda x: (
                self._priority_score(x[0]),
                0 if x[1].is_available else 1,
                x[1].response_time or float('inf'),
                -x[1].success_rate
            )
        )

        return best_source

    def _priority_score(self, config: DataSourceConfig) -> int:
        """
        获取数据源优先级分数（越小优先级越高）

        Args:
            config: 数据源配置

        Returns:
            优先级分数
        """
        priority_scores = {
            DataSourcePriority.PRIMARY: 0,
            DataSourcePriority.SECONDARY: 1,
            DataSourcePriority.FALLBACK: 2
        }
        return priority_scores.get(config.settings.priority, 3)

    async def _check_source_availability(self, config: DataSourceConfig,
                                       status: Optional[DataSourceStatus]) -> bool:
        """
        检查数据源可用性

        Args:
            config: 数据源配置
            status: 数据源状态

        Returns:
            是否可用
        """
        try:
            # 如果最近检查过且状态良好，直接返回
            if (status and status.last_check_time and
                datetime.now() - status.last_check_time < timedelta(minutes=5) and
                status.is_available):
                return True

            # 执行实际的健康检查
            start_time = datetime.now()
            is_available = await self._perform_health_check(config)
            response_time = (datetime.now() - start_time).total_seconds()

            # 更新状态
            if status:
                status.is_available = is_available
                status.last_check_time = datetime.now()
                status.response_time = response_time
                if is_available:
                    status.last_success_time = datetime.now()

                self.logger.info(f"数据源 {config.name} 健康检查: {'通过' if is_available else '失败'} "
                               f"(响应时间: {response_time:.2f}s)")

            return is_available

        except Exception as e:
            self.logger.error(f"检查数据源 {config.name} 可用性失败: {e}")
            if status:
                status.is_available = False
                status.last_check_time = datetime.now()
                status.error_message = str(e)
            return False

    async def _perform_health_check(self, config: DataSourceConfig) -> bool:
        """
        执行数据源健康检查

        Args:
            config: 数据源配置

        Returns:
            是否健康
        """
        try:
            # 根据数据源类型执行不同的健康检查
            if config.source_type == DataSourceType.TUSHARE:
                return await self._check_tushare_health(config)
            elif config.source_type == DataSourceType.BAOSTOCK:
                return await self._check_baostock_health(config)
            elif config.source_type == DataSourceType.YAHOO:
                return await self._check_yahoo_health(config)
            else:
                # 对于其他数据源，尝试创建实例
                return await self._check_generic_health(config)

        except Exception as e:
            self.logger.debug(f"健康检查失败: {e}")
            return False

    async def _check_tushare_health(self, config: DataSourceConfig) -> bool:
        """检查Tushare数据源健康状态"""
        try:
            from ..services.data.tushare_market_service import TushareMarketService
            from ..config.tushare_config import TushareConfig

            # 创建配置
            tushare_config = TushareConfig(
                token=config.credentials.token,
                cache_enabled=False,  # 健康检查不使用缓存
                rate_limit=1  # 健康检查限制请求频率
            )

            # 创建服务实例
            service = TushareMarketService(tushare_config)

            # 执行连接测试
            result = await service.test_connection()
            return result['success']

        except Exception:
            return False

    async def _check_baostock_health(self, config: DataSourceConfig) -> bool:
        """检查Baostock数据源健康状态"""
        try:
            from ..baostock_source import BaostockDataSource

            # 创建数据源实例
            source = BaostockDataSource()

            # 尝试登录
            import baostock as bs
            lg = bs.login()
            bs.logout()

            return lg.error_code == '0'

        except Exception:
            return False

    async def _check_yahoo_health(self, config: DataSourceConfig) -> bool:
        """检查Yahoo Finance数据源健康状态"""
        try:
            import yfinance as yf

            # 尝试获取一个知名股票的信息
            ticker = yf.Ticker("AAPL")
            info = ticker.info

            return bool(info)

        except Exception:
            return False

    async def _check_generic_health(self, config: DataSourceConfig) -> bool:
        """通用健康检查"""
        try:
            # 尝试通过DataFactory创建数据源实例
            source = DataFactory.get_source(config.name.lower())

            if source:
                # 尝试调用test_connection（如果存在）
                if hasattr(source, 'test_connection'):
                    if asyncio.iscoroutinefunction(source.test_connection):
                        result = await source.test_connection()
                    else:
                        result = source.test_connection()
                    return bool(result) if isinstance(result, bool) else True
                else:
                    return True

            return False

        except Exception:
            return False

    async def get_data_source_instance(self, source_name: str) -> Optional[DataSource]:
        """
        获取数据源实例

        Args:
            source_name: 数据源名称

        Returns:
            数据源实例
        """
        try:
            config = self.config_manager.get_data_source(source_name)
            if not config or not config.settings.enabled:
                return None

            # 根据数据源类型创建实例
            if config.source_type == DataSourceType.TUSHARE:
                from ..services.data.tushare_market_service import TushareMarketService
                from ..config.tushare_config import TushareConfig

                tushare_config = TushareConfig(
                    token=config.credentials.token,
                    cache_enabled=config.settings.cache_enabled,
                    cache_ttl=config.settings.cache_ttl,
                    rate_limit=config.settings.rate_limit,
                    timeout=config.credentials.timeout,
                    retry_times=config.credentials.retry_times
                )

                service = TushareMarketService(tushare_config)
                from ..adapters.tushare_service_adapter import TushareServiceAdapter
                return TushareServiceAdapter(tushare_config)

            elif config.source_type == DataSourceType.BAOSTOCK:
                return DataFactory.get_source("baostock")

            else:
                # 尝试通过DataFactory获取
                return DataFactory.get_source(config.name.lower())

        except Exception as e:
            self.logger.error(f"获取数据源实例失败: {e}")
            return None

    async def execute_with_fallback(self, request: DataSourceRequest,
                                  method_name: str, *args, **kwargs) -> Any:
        """
        执行数据请求，支持自动降级到备用数据源

        Args:
            request: 数据源请求上下文
            method_name: 要调用的方法名
            *args: 方法参数
            **kwargs: 方法关键字参数

        Returns:
            方法执行结果
        """
        selected_sources = []

        # 选择最佳数据源
        best_source_name = await self.select_best_source(request)

        if not best_source_name:
            raise Exception("没有可用的数据源")

        selected_sources.append(best_source_name)

        # 如果启用了备用数据源，获取其他可用的数据源
        if request.fallback_enabled:
            enabled_sources = self.config_manager.get_data_sources_by_priority()
            for source in enabled_sources:
                if source.name not in selected_sources and source.name != best_source_name:
                    suitable = await self._filter_suitable_sources([source], request)
                    if suitable and await self._check_source_availability(source, None):
                        selected_sources.append(source.name)

        # 尝试执行请求
        last_error = None
        for source_name in selected_sources:
            try:
                source_instance = await self.get_data_source_instance(source_name)
                if not source_instance:
                    continue

                method = getattr(source_instance, method_name)

                # 执行方法（支持异步和同步）
                if asyncio.iscoroutinefunction(method):
                    result = await method(*args, **kwargs)
                else:
                    result = method(*args, **kwargs)

                # 更新成功状态
                self._update_source_success_status(source_name)
                self.request_stats['successful_requests'] += 1

                # 如果使用了备用数据源，记录统计
                if source_name != best_source_name:
                    self.request_stats['fallback_used'] += 1
                    self.logger.info(f"使用备用数据源 {source_name} 成功处理请求")

                return result

            except Exception as e:
                last_error = e
                self._update_source_error_status(source_name, str(e))
                self.logger.warning(f"数据源 {source_name} 执行失败: {e}")

                # 如果还有备用数据源，继续尝试
                if source_name != selected_sources[-1]:
                    continue

        # 所有数据源都失败了
        self.request_stats['failed_requests'] += 1
        raise Exception(f"所有数据源都失败了，最后错误: {last_error}")

    def _update_source_success_status(self, source_name: str):
        """更新数据源成功状态"""
        status = self.source_status.get(source_name)
        if status:
            # 更新成功率（简单的滑动平均）
            status.success_rate = min(1.0, status.success_rate * 0.9 + 0.1)
            status.last_success_time = datetime.now()
            status.error_message = None

    def _update_source_error_status(self, source_name: str, error_message: str):
        """更新数据源错误状态"""
        status = self.source_status.get(source_name)
        if status:
            status.is_available = False
            status.last_check_time = datetime.now()
            status.error_message = error_message
            # 降低成功率
            status.success_rate = max(0.0, status.success_rate * 0.8)

    def get_source_status(self, source_name: str) -> Optional[DataSourceStatus]:
        """获取数据源状态"""
        return self.source_status.get(source_name)

    def get_all_source_status(self) -> Dict[str, DataSourceStatus]:
        """获取所有数据源状态"""
        return self.source_status.copy()

    def get_request_stats(self) -> Dict[str, Any]:
        """获取请求统计信息"""
        return self.request_stats.copy()

    async def refresh_all_source_status(self):
        """刷新所有数据源状态"""
        for name, config in self.config_manager.get_all_data_sources().items():
            if config.settings.enabled:
                await self._check_source_availability(
                    config,
                    self.source_status.get(name)
                )

    def get_recommended_config(self) -> Dict[str, Any]:
        """获取推荐的配置建议"""
        enabled_sources = self.config_manager.get_enabled_data_sources()
        source_count = len(enabled_sources)

        recommendations = []

        if source_count == 0:
            recommendations.append({
                'level': 'warning',
                'message': '没有启用的数据源，建议至少启用一个数据源'
            })
        elif source_count == 1:
            recommendations.append({
                'level': 'info',
                'message': '只启用了一个数据源，建议启用多个数据源作为备份'
            })

        # 检查主要数据源
        primary_sources = [s for s in enabled_sources.values()
                          if s.settings.priority == DataSourcePriority.PRIMARY]

        if not primary_sources:
            recommendations.append({
                'level': 'warning',
                'message': '没有设置主要数据源，建议设置一个主要数据源'
            })

        # 检查数据源健康状态
        unhealthy_sources = [name for name, status in self.source_status.items()
                           if status.is_available is False]

        if unhealthy_sources:
            recommendations.append({
                'level': 'error',
                'message': f'数据源 {", ".join(unhealthy_sources)} 不可用，请检查配置'
            })

        return {
            'total_sources': len(self.config_manager.get_all_data_sources()),
            'enabled_sources': source_count,
            'healthy_sources': len([s for s in self.source_status.values() if s.is_available]),
            'recommendations': recommendations
        }


# 全局选择器实例
_global_selector: Optional[DataSourceSelector] = None


def get_data_source_selector() -> DataSourceSelector:
    """获取全局数据源选择器实例"""
    global _global_selector
    if _global_selector is None:
        _global_selector = DataSourceSelector()
    return _global_selector


def init_data_source_selector(config_manager: Optional[DataSourceManager] = None) -> DataSourceSelector:
    """初始化全局数据源选择器"""
    global _global_selector
    _global_selector = DataSourceSelector(config_manager)
    return _global_selector