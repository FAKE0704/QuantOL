"""
Tushare市场数据服务 - 协调各组件的主要服务类
职责：整合TushareAdapter、DataTransformer、CacheManager等组件，提供统一的数据服务接口
"""

import asyncio
import logging
import time
import pandas as pd
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime, timedelta
import threading
from collections import defaultdict

from src.core.data.adapters.tushare_adapter import TushareAdapter, TushareAdapterError
from src.core.data.transformers.data_transformer import DataTransformer, DataTransformerError
from src.core.data.cache.cache_manager import CacheManager, CacheError
from src.core.data.config.tushare_config import TushareConfig


class TushareServiceError(Exception):
    """Tushare服务错误"""
    pass


class RateLimiter:
    """请求频率限制器"""

    def __init__(self, max_requests_per_minute: int = 120):
        self.max_requests = max_requests_per_minute
        self.requests = []
        self.lock = threading.Lock()

    def acquire(self) -> bool:
        """
        获取请求许可

        Returns:
            是否可以立即请求
        """
        with self.lock:
            now = time.time()
            # 清理一分钟前的请求记录
            self.requests = [req_time for req_time in self.requests if now - req_time < 60]

            if len(self.requests) < self.max_requests:
                self.requests.append(now)
                return True

            return False

    def wait_if_needed(self) -> None:
        """等待直到可以请求"""
        while not self.acquire():
            time.sleep(1)


class TushareMarketService:
    """Tushare市场数据服务 - 协调各组件"""

    def __init__(self, config: TushareConfig):
        """
        初始化Tushare市场服务

        Args:
            config: Tushare配置
        """
        self.config = config
        self.logger = self._setup_logger()

        # 初始化组件
        self.adapter = TushareAdapter(config.token)
        self.transformer = DataTransformer()
        self.cache = CacheManager(config.cache_dir, config.cache_ttl) if config.cache_enabled else None
        self.rate_limiter = RateLimiter(config.rate_limit)

        # 请求统计
        self.request_stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'last_request_time': None
        }

        self.logger.info("Tushare市场服务初始化完成")

    def _setup_logger(self) -> logging.Logger:
        """设置日志"""
        logger = logging.getLogger(f"{__name__}.{id(self)}")
        logger.setLevel(getattr(logging, self.config.log_level.upper()))

        # 如果还没有handler，添加一个
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger

    def _get_cache_key(self, method: str, **kwargs) -> str:
        """生成缓存键"""
        if self.cache:
            return self.cache.get_cache_key(method, **kwargs)
        return ""

    def _update_request_stats(self, success: bool, cache_hit: bool = False) -> None:
        """更新请求统计"""
        self.request_stats['total_requests'] += 1
        if success:
            self.request_stats['successful_requests'] += 1
        else:
            self.request_stats['failed_requests'] += 1

        if cache_hit:
            self.request_stats['cache_hits'] += 1
        else:
            self.request_stats['cache_misses'] += 1

        self.request_stats['last_request_time'] = datetime.now()

    async def get_stock_list(self, use_cache: bool = True, exchange: str = '', list_status: str = 'L') -> pd.DataFrame:
        """
        获取股票列表（带缓存）

        Args:
            use_cache: 是否使用缓存
            exchange: 交易所代码
            list_status: 上市状态

        Returns:
            标准化的股票列表DataFrame
        """
        method_name = "get_stock_list"
        cache_key = self._get_cache_key(method_name, exchange=exchange, list_status=list_status)

        try:
            # 检查缓存
            if use_cache and self.cache and cache_key:
                cached_data = self.cache.load(cache_key)
                if cached_data is not None:
                    self.logger.debug("股票列表缓存命中")
                    self._update_request_stats(True, cache_hit=True)
                    return cached_data

            # 频率控制
            self.rate_limiter.wait_if_needed()

            # 获取数据
            raw_data = self.adapter.get_stock_basic(exchange=exchange, list_status=list_status)

            # 数据转换
            transformed_data = self.transformer.transform_stock_basic(raw_data, source='tushare')

            # 验证数据
            validation_result = self.transformer.validate_transformed_data(transformed_data, 'stock_basic')
            if not validation_result['valid']:
                self.logger.warning(f"股票列表数据验证失败: {validation_result['errors']}")

            # 保存缓存
            if use_cache and self.cache and cache_key:
                self.cache.save(cache_key, transformed_data, ttl=self.config.cache_ttl, tags=['stock_basic'])

            self._update_request_stats(True)
            self.logger.info(f"成功获取股票列表，共 {len(transformed_data)} 条记录")

            return transformed_data

        except (TushareAdapterError, DataTransformerError) as e:
            self._update_request_stats(False)
            self.logger.error(f"获取股票列表失败: {e}")
            raise TushareServiceError(f"获取股票列表失败: {e}")

    async def get_market_data(self, symbol_code: str, start_date: str, end_date: str,
                            frequency: str = 'D', use_cache: bool = True) -> pd.DataFrame:
        """
        获取市场数据（带缓存和限流）

        Args:
            symbol_code: 股票代码（包含交易所后缀）
            start_date: 开始日期
            end_date: 结束日期
            frequency: 频率（D日线，W周线，M月线）
            use_cache: 是否使用缓存

        Returns:
            标准化的市场数据DataFrame
        """
        method_name = "get_market_data"
        cache_key = self._get_cache_key(method_name, symbol_code=symbol_code,
                                     start_date=start_date, end_date=end_date, frequency=frequency)

        try:
            # 检查缓存
            if use_cache and self.cache and cache_key:
                cached_data = self.cache.load(cache_key)
                if cached_data is not None:
                    self.logger.debug(f"市场数据缓存命中: {symbol_code}")
                    self._update_request_stats(True, cache_hit=True)
                    return cached_data

            # 频率控制
            self.rate_limiter.wait_if_needed()

            # 获取数据
            raw_data = self.adapter.get_daily_data(symbol_code, start_date, end_date)

            # 数据转换
            transformed_data = self.transformer.transform_market_data(raw_data, source='tushare')

            # 验证数据
            validation_result = self.transformer.validate_transformed_data(transformed_data, 'market_data')
            if not validation_result['valid']:
                self.logger.warning(f"市场数据验证失败: {validation_result['errors']}")

            # 保存缓存
            if use_cache and self.cache and cache_key:
                self.cache.save(cache_key, transformed_data, ttl=self.config.cache_ttl, tags=['market_data'])

            self._update_request_stats(True)
            self.logger.info(f"成功获取市场数据 {symbol_code}，共 {len(transformed_data)} 条记录")

            return transformed_data

        except (TushareAdapterError, DataTransformerError) as e:
            self._update_request_stats(False)
            self.logger.error(f"获取市场数据失败: {e}")
            raise TushareServiceError(f"获取市场数据失败: {e}")

    async def get_financial_data(self, symbol_code: str, start_date: str, end_date: str,
                               report_type: str = '1', use_cache: bool = True) -> pd.DataFrame:
        """
        获取财务数据

        Args:
            symbol_code: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            report_type: 报告类型
            use_cache: 是否使用缓存

        Returns:
            标准化的财务数据DataFrame
        """
        method_name = "get_financial_data"
        cache_key = self._get_cache_key(method_name, symbol_code=symbol_code,
                                     start_date=start_date, end_date=end_date, report_type=report_type)

        try:
            # 检查缓存
            if use_cache and self.cache and cache_key:
                cached_data = self.cache.load(cache_key)
                if cached_data is not None:
                    self.logger.debug(f"财务数据缓存命中: {symbol_code}")
                    self._update_request_stats(True, cache_hit=True)
                    return cached_data

            # 频率控制
            self.rate_limiter.wait_if_needed()

            # 获取数据
            raw_data = self.adapter.get_financial_data(symbol_code, start_date, end_date, report_type)

            # 数据转换
            transformed_data = self.transformer.transform_financial_data(raw_data, source='tushare')

            # 保存缓存
            if use_cache and self.cache and cache_key:
                self.cache.save(cache_key, transformed_data, ttl=self.config.cache_ttl, tags=['financial_data'])

            self._update_request_stats(True)
            self.logger.info(f"成功获取财务数据 {symbol_code}，共 {len(transformed_data)} 条记录")

            return transformed_data

        except (TushareAdapterError, DataTransformerError) as e:
            self._update_request_stats(False)
            self.logger.error(f"获取财务数据失败: {e}")
            raise TushareServiceError(f"获取财务数据失败: {e}")

    async def get_realtime_quotes(self, symbol_codes: List[str], use_cache: bool = False) -> pd.DataFrame:
        """
        获取实时行情

        Args:
            symbol_codes: 股票代码列表
            use_cache: 是否使用缓存（实时数据通常不缓存）

        Returns:
            实时行情DataFrame
        """
        method_name = "get_realtime_quotes"
        cache_key = self._get_cache_key(method_name, symbol_codes=symbol_codes)

        try:
            # 检查缓存（实时数据缓存时间很短）
            if use_cache and self.cache and cache_key:
                cached_data = self.cache.load(cache_key)
                if cached_data is not None:
                    self.logger.debug("实时行情缓存命中")
                    self._update_request_stats(True, cache_hit=True)
                    return cached_data

            # 频率控制
            self.rate_limiter.wait_if_needed()

            # 获取数据
            raw_data = self.adapter.get_realtime_quote(symbol_codes)

            # 保存缓存（如果启用，缓存时间很短）
            if use_cache and self.cache and cache_key:
                self.cache.save(cache_key, raw_data, ttl=60, tags=['realtime'])  # 只缓存1分钟

            self._update_request_stats(True)
            self.logger.info(f"成功获取实时行情，共 {len(raw_data)} 条记录")

            return raw_data

        except TushareAdapterError as e:
            self._update_request_stats(False)
            self.logger.error(f"获取实时行情失败: {e}")
            raise TushareServiceError(f"获取实时行情失败: {e}")

    async def get_index_basic(self, exchange: str = '', market: str = '', use_cache: bool = True) -> pd.DataFrame:
        """
        获取指数基本信息

        Args:
            exchange: 交易所代码
            market: 市场代码
            use_cache: 是否使用缓存

        Returns:
            指数基本信息DataFrame
        """
        method_name = "get_index_basic"
        cache_key = self._get_cache_key(method_name, exchange=exchange, market=market)

        try:
            # 检查缓存
            if use_cache and self.cache and cache_key:
                cached_data = self.cache.load(cache_key)
                if cached_data is not None:
                    self.logger.debug("指数基本信息缓存命中")
                    self._update_request_stats(True, cache_hit=True)
                    return cached_data

            # 频率控制
            self.rate_limiter.wait_if_needed()

            # 获取数据
            raw_data = self.adapter.get_index_basic(exchange, market)

            # 数据转换
            transformed_data = self.transformer.transform_index_data(raw_data, source='tushare')

            # 保存缓存
            if use_cache and self.cache and cache_key:
                self.cache.save(cache_key, transformed_data, ttl=self.config.cache_ttl, tags=['index_basic'])

            self._update_request_stats(True)
            self.logger.info(f"成功获取指数基本信息，共 {len(transformed_data)} 条记录")

            return transformed_data

        except (TushareAdapterError, DataTransformerError) as e:
            self._update_request_stats(False)
            self.logger.error(f"获取指数基本信息失败: {e}")
            raise TushareServiceError(f"获取指数基本信息失败: {e}")

    async def test_connection(self) -> Dict[str, Any]:
        """
        测试连接

        Returns:
            连接测试结果
        """
        try:
            # 测试适配器连接
            adapter_ok = self.adapter.test_connection()

            # 测试缓存（如果启用）
            cache_ok = True
            if self.cache:
                cache_ok = self.cache.get_cache_info() is not None

            result = {
                'success': adapter_ok,
                'adapter_connected': adapter_ok,
                'cache_available': cache_ok,
                'config_valid': self.config.validate(),
                'timestamp': datetime.now().isoformat()
            }

            if result['success']:
                self.logger.info("Tushare服务连接测试成功")
            else:
                self.logger.warning("Tushare服务连接测试失败")

            return result

        except Exception as e:
            self.logger.error(f"连接测试失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

    async def get_service_stats(self) -> Dict[str, Any]:
        """
        获取服务统计信息

        Returns:
            服务统计信息
        """
        stats = {
            'service_stats': self.request_stats.copy(),
            'config': {
                'cache_enabled': self.config.cache_enabled,
                'rate_limit': self.config.rate_limit,
                'cache_ttl': self.config.cache_ttl
            }
        }

        # 添加缓存统计
        if self.cache:
            stats['cache_stats'] = self.cache.get_cache_info()

        return stats

    async def clear_cache(self, pattern: str = None, tags: List[str] = None) -> Dict[str, Any]:
        """
        清理缓存

        Args:
            pattern: 缓存键模式
            tags: 缓存标签

        Returns:
            清理结果
        """
        if not self.cache:
            return {'success': False, 'message': '缓存未启用'}

        try:
            cleared_count = self.cache.clear(pattern=pattern, tags=tags)
            return {
                'success': True,
                'cleared_count': cleared_count,
                'message': f'成功清理 {cleared_count} 个缓存项'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    async def optimize_cache(self, max_size_mb: float = 1024) -> Dict[str, Any]:
        """
        优化缓存

        Args:
            max_size_mb: 最大缓存大小

        Returns:
            优化结果
        """
        if not self.cache:
            return {'success': False, 'message': '缓存未启用'}

        try:
            result = self.cache.optimize_cache(max_size_mb)
            return {
                'success': True,
                'result': result
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    async def batch_get_market_data(self, symbol_codes: List[str], start_date: str, end_date: str,
                                   frequency: str = 'D', use_cache: bool = True,
                                   max_concurrent: int = 5) -> Dict[str, pd.DataFrame]:
        """
        批量获取市场数据

        Args:
            symbol_codes: 股票代码列表
            start_date: 开始日期
            end_date: 结束日期
            frequency: 频率
            use_cache: 是否使用缓存
            max_concurrent: 最大并发数

        Returns:
            股票代码到数据的映射字典
        """
        semaphore = asyncio.Semaphore(max_concurrent)

        async def get_single_symbol(symbol: str) -> Tuple[str, pd.DataFrame]:
            async with semaphore:
                try:
                    data = await self.get_market_data(
                        symbol, start_date, end_date, frequency, use_cache
                    )
                    return symbol, data
                except Exception as e:
                    self.logger.error(f"获取 {symbol} 数据失败: {e}")
                    return symbol, pd.DataFrame()

        # 并发获取数据
        tasks = [get_single_symbol(symbol) for symbol in symbol_codes]
        results = await asyncio.gather(*tasks)

        # 转换为字典
        return {symbol: data for symbol, data in results}

    def __del__(self):
        """析构函数"""
        if hasattr(self, 'logger'):
            self.logger.debug("Tushare市场服务销毁")