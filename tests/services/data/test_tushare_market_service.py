"""
TushareMarketService测试
测试tushare市场数据服务的各项功能
"""

import unittest
import pandas as pd
from unittest.mock import Mock, patch, AsyncMock, MagicMock
import asyncio
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../..'))

from src.services.data.tushare_market_service import (
    TushareMarketService, TushareServiceError, RateLimiter
)
from src.core.data.config.tushare_config import TushareConfig


class TestRateLimiter(unittest.TestCase):
    """RateLimiter测试类"""

    def setUp(self):
        """测试前设置"""
        self.rate_limiter = RateLimiter(max_requests_per_minute=60)

    @patch('src.services.data.tushare_market_service.time')
    def test_acquire_first_request(self, mock_time):
        """测试第一个请求"""
        mock_time.time.return_value = 1000.0

        result = self.rate_limiter.acquire()
        self.assertTrue(result)
        self.assertEqual(len(self.rate_limiter.requests), 1)
        self.assertEqual(self.rate_limiter.requests[0], 1000.0)

    @patch('src.services.data.tushare_market_service.time')
    def test_acquire_under_limit(self, mock_time):
        """测试未超过频率限制"""
        mock_time.time.side_effect = [1000.0, 1000.5]  # 模拟两次请求时间

        # 第一次请求
        result1 = self.rate_limiter.acquire()
        self.assertTrue(result1)

        # 第二次请求（未超过限制）
        result2 = self.rate_limiter.acquire()
        self.assertTrue(result2)

    @patch('src.services.data.tushare_market_service.time')
    def test_acquire_over_limit(self, mock_time):
        """测试超过频率限制"""
        # 模拟60个请求在同一分钟内
        mock_time.time.return_value = 1000.0

        # 先添加60个请求（达到限制）
        for _ in range(60):
            self.rate_limiter.acquire()

        # 第61个请求应该被拒绝
        result = self.rate_limiter.acquire()
        self.assertFalse(result)

    @patch('src.services.data.tushare_market_service.time.sleep')
    def test_wait_if_needed(self, mock_sleep):
        """测试等待机制"""
        # 模拟已达到限制
        for _ in range(60):
            self.rate_limiter.acquire()

        # 调用wait_if_needed应该调用sleep
        self.rate_limiter.wait_if_needed()
        mock_sleep.assert_called()


class TestTushareMarketService(unittest.IsolatedAsyncioTestCase):
    """TushareMarketService测试类"""

    def setUp(self):
        """测试前设置"""
        self.config = TushareConfig(
            token="test_token",
            cache_enabled=False,  # 禁用缓存以便测试
            rate_limit=60
        )
        self.service = TushareMarketService(self.config)

    def setUp_mock_cache(self):
        """设置模拟缓存"""
        self.mock_cache = AsyncMock()
        self.service.cache = self.mock_cache

    def setUp_mock_components(self):
        """设置模拟组件"""
        # 模拟适配器
        self.mock_adapter = AsyncMock()
        self.service.adapter = self.mock_adapter

        # 模拟转换器
        self.mock_transformer = AsyncMock()
        self.service.transformer = self.mock_transformer

        # 模拟缓存
        self.mock_cache = AsyncMock()
        self.service.cache = self.mock_cache

    async def test_init(self):
        """测试初始化"""
        self.assertEqual(self.service.config, self.config)
        self.assertIsNotNone(self.service.adapter)
        self.assertIsNotNone(self.service.transformer)
        self.assertIsNone(self.service.cache)  # 因为cache_enabled=False

    async def test_get_stock_list_cache_hit(self):
        """测试股票列表缓存命中"""
        self.setUp_mock_cache()
        cache_key = "test_cache_key"
        expected_data = pd.DataFrame({'symbol': ['000001'], 'name': ['测试股票']})

        with patch.object(self.service, '_get_cache_key', return_value=cache_key):
            self.mock_cache.load.return_value = expected_data

            result = await self.service.get_stock_list()

            self.mock_cache.load.assert_called_once_with(cache_key)
            pd.testing.assert_frame_equal(result, expected_data)
            # 验证没有调用适配器
            self.service.adapter.get_stock_basic.assert_not_called()

    async def test_get_stock_list_cache_miss(self):
        """测试股票列表缓存未命中"""
        self.setUp_mock_cache()
        self.setUp_mock_components()

        cache_key = "test_cache_key"
        raw_data = pd.DataFrame({'ts_code': ['000001.SZ'], 'name': ['平安银行']})
        transformed_data = pd.DataFrame({'symbol_code': ['000001.SZ'], 'name': ['平安银行']})

        with patch.object(self.service, '_get_cache_key', return_value=cache_key):
            # 模拟缓存未命中
            self.mock_cache.load.return_value = None
            # 模拟适配器返回原始数据
            self.mock_adapter.get_stock_basic.return_value = raw_data
            # 模拟转换器返回转换后数据
            self.mock_transformer.transform_stock_basic.return_value = transformed_data

            result = await self.service.get_stock_list()

            # 验证调用顺序
            self.mock_cache.load.assert_called_once_with(cache_key)
            self.mock_adapter.get_stock_basic.assert_called_once()
            self.mock_transformer.transform_stock_basic.assert_called_once_with(raw_data, source='tushare')
            self.mock_cache.save.assert_called_once()

            pd.testing.assert_frame_equal(result, transformed_data)

    async def test_get_stock_list_no_cache(self):
        """测试不使用缓存的股票列表获取"""
        self.setUp_mock_components()

        raw_data = pd.DataFrame({'ts_code': ['000001.SZ'], 'name': ['平安银行']})
        transformed_data = pd.DataFrame({'symbol_code': ['000001.SZ'], 'name': ['平安银行']})

        # 模拟适配器和转换器
        self.mock_adapter.get_stock_basic.return_value = raw_data
        self.mock_transformer.transform_stock_basic.return_value = transformed_data

        result = await self.service.get_stock_list(use_cache=False)

        # 验证调用
        self.mock_adapter.get_stock_basic.assert_called_once()
        self.mock_transformer.transform_stock_basic.assert_called_once_with(raw_data, source='tushare')

        pd.testing.assert_frame_equal(result, transformed_data)

    async def test_get_stock_list_adapter_error(self):
        """测试适配器错误处理"""
        self.setUp_mock_components()
        self.mock_adapter.get_stock_basic.side_effect = Exception("API Error")

        with self.assertRaises(TushareServiceError):
            await self.service.get_stock_list()

    async def test_get_market_data_success(self):
        """测试成功获取市场数据"""
        self.setUp_mock_components()

        raw_data = pd.DataFrame({
            'ts_code': ['000001.SZ'],
            'trade_date': ['20240101'],
            'open': [10.0],
            'close': [11.0]
        })
        transformed_data = pd.DataFrame({
            'symbol_code': ['000001.SZ'],
            'date': ['2024-01-01'],
            'open': [10.0],
            'close': [11.0]
        })

        self.mock_adapter.get_daily_data.return_value = raw_data
        self.mock_transformer.transform_market_data.return_value = transformed_data

        result = await self.service.get_market_data('000001.SZ', '20240101', '20240102')

        self.mock_adapter.get_daily_data.assert_called_once_with('000001.SZ', '20240101', '20240102')
        self.mock_transformer.transform_market_data.assert_called_once_with(raw_data, source='tushare')

        pd.testing.assert_frame_equal(result, transformed_data)

    async def test_get_financial_data_success(self):
        """测试成功获取财务数据"""
        self.setUp_mock_components()

        raw_data = pd.DataFrame({
            'ts_code': ['000001.SZ'],
            'end_date': ['20231231'],
            'total_revenue': [1000000]
        })
        transformed_data = pd.DataFrame({
            'symbol_code': ['000001.SZ'],
            'report_date': ['2023-12-31'],
            'total_revenue': [1000000]
        })

        self.mock_adapter.get_financial_data.return_value = raw_data
        self.mock_transformer.transform_financial_data.return_value = transformed_data

        result = await self.service.get_financial_data('000001.SZ', '20230101', '20231231')

        self.mock_adapter.get_financial_data.assert_called_once_with('000001.SZ', '20230101', '20231231', '1')
        self.mock_transformer.transform_financial_data.assert_called_once_with(raw_data, source='tushare')

        pd.testing.assert_frame_equal(result, transformed_data)

    async def test_get_realtime_quotes_success(self):
        """测试成功获取实时行情"""
        self.setUp_mock_components()

        raw_data = pd.DataFrame({
            'ts_code': ['000001.SZ'],
            'price': [10.5],
            'change': [0.5]
        })

        self.mock_adapter.get_realtime_quote.return_value = raw_data

        result = await self.service.get_realtime_quotes(['000001.SZ'])

        self.mock_adapter.get_realtime_quote.assert_called_once_with(['000001.SZ'])

        pd.testing.assert_frame_equal(result, raw_data)

    async def test_get_index_basic_success(self):
        """测试成功获取指数基本信息"""
        self.setUp_mock_components()

        raw_data = pd.DataFrame({
            'ts_code': ['000001.SH'],
            'name': ['上证指数']
        })
        transformed_data = pd.DataFrame({
            'symbol_code': ['000001.SH'],
            'name': ['上证指数']
        })

        self.mock_adapter.get_index_basic.return_value = raw_data
        self.mock_transformer.transform_index_data.return_value = transformed_data

        result = await self.service.get_index_basic(exchange='SSE')

        self.mock_adapter.get_index_basic.assert_called_once_with('SSE', '')
        self.mock_transformer.transform_index_data.assert_called_once_with(raw_data, source='tushare')

        pd.testing.assert_frame_equal(result, transformed_data)

    async def test_test_connection_success(self):
        """测试连接成功"""
        self.service.adapter.test_connection.return_value = True

        result = await self.service.test_connection()

        self.assertTrue(result['success'])
        self.assertTrue(result['adapter_connected'])
        self.assertTrue(result['config_valid'])

    async def test_test_connection_failure(self):
        """测试连接失败"""
        self.service.adapter.test_connection.return_value = False

        result = await self.service.test_connection()

        self.assertFalse(result['success'])
        self.assertFalse(result['adapter_connected'])

    async def test_get_service_stats(self):
        """测试获取服务统计"""
        # 模拟一些请求
        self.service.request_stats['total_requests'] = 10
        self.service.request_stats['successful_requests'] = 8

        stats = await self.service.get_service_stats()

        self.assertEqual(stats['service_stats']['total_requests'], 10)
        self.assertEqual(stats['service_stats']['successful_requests'], 8)
        self.assertIn('config', stats)

    async def test_clear_cache_success(self):
        """测试成功清理缓存"""
        self.setUp_mock_cache()
        self.mock_cache.clear.return_value = 5

        result = await self.service.clear_cache()

        self.assertTrue(result['success'])
        self.assertEqual(result['cleared_count'], 5)

    async def test_clear_cache_not_enabled(self):
        """测试缓存未启用时的清理"""
        self.service.cache = None

        result = await self.service.clear_cache()

        self.assertFalse(result['success'])
        self.assertIn('未启用', result['message'])

    async def test_optimize_cache_success(self):
        """测试成功优化缓存"""
        self.setUp_mock_cache()
        self.mock_cache.optimize_cache.return_value = {'expired_cleaned': 3, 'final_size_mb': 500}

        result = await self.service.optimize_cache()

        self.assertTrue(result['success'])
        self.assertEqual(result['result']['expired_cleaned'], 3)

    async def test_batch_get_market_data(self):
        """测试批量获取市场数据"""
        self.setUp_mock_components()

        # 模拟单个股票数据获取
        async def mock_get_market_data(symbol, start_date, end_date, frequency, use_cache):
            return pd.DataFrame({
                'symbol_code': [symbol],
                'date': [start_date],
                'close': [10.0]
            })

        with patch.object(self.service, 'get_market_data', side_effect=mock_get_market_data):
            symbols = ['000001.SZ', '000002.SZ']
            result = await self.service.batch_get_market_data(symbols, '20240101', '20240102', max_concurrent=2)

            self.assertEqual(len(result), 2)
            self.assertIn('000001.SZ', result)
            self.assertIn('000002.SZ', result)
            self.assertEqual(len(result['000001.SZ']), 1)
            self.assertEqual(len(result['000002.SZ']), 1)

    async def test_data_validation_warning(self):
        """测试数据验证警告"""
        self.setUp_mock_components()

        # 模拟转换器返回验证失败的数据
        raw_data = pd.DataFrame({'ts_code': ['000001.SZ']})
        transformed_data = pd.DataFrame({'symbol_code': ['000001.SZ']})

        self.mock_adapter.get_stock_basic.return_value = raw_data
        self.mock_transformer.transform_stock_basic.return_value = transformed_data
        self.mock_transformer.validate_transformed_data.return_value = {
            'valid': False,
            'errors': ['Missing required field'],
            'warnings': [],
            'stats': {}
        }

        with patch.object(self.service, 'logger') as mock_logger:
            result = await self.service.get_stock_list()

            # 应该仍然返回数据，但记录警告
            pd.testing.assert_frame_equal(result, transformed_data)
            mock_logger.warning.assert_called()

    def test_update_request_stats(self):
        """测试请求统计更新"""
        initial_stats = self.service.request_stats.copy()

        # 测试成功请求
        self.service._update_request_stats(True)
        self.assertEqual(self.service.request_stats['total_requests'], initial_stats['total_requests'] + 1)
        self.assertEqual(self.service.request_stats['successful_requests'], initial_stats['successful_requests'] + 1)

        # 测试失败请求
        self.service._update_request_stats(False)
        self.assertEqual(self.service.request_stats['total_requests'], initial_stats['total_requests'] + 2)
        self.assertEqual(self.service.request_stats['failed_requests'], initial_stats['failed_requests'] + 1)

        # 测试缓存命中
        self.service._update_request_stats(True, cache_hit=True)
        self.assertEqual(self.service.request_stats['cache_hits'], initial_stats['cache_hits'] + 1)


if __name__ == '__main__':
    unittest.main()