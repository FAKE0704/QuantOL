"""
TushareAdapter测试
测试tushare数据源适配器的各项功能
"""

import unittest
import pandas as pd
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../../'))

from src.core.data.adapters.tushare_adapter import TushareAdapter, TushareAdapterError


class TestTushareAdapter(unittest.TestCase):
    """TushareAdapter测试类"""

    def setUp(self):
        """测试前设置"""
        self.test_token = "test_token_12345"
        self.adapter = TushareAdapter(self.test_token)

    def test_init(self):
        """测试初始化"""
        adapter = TushareAdapter("test_token")
        self.assertEqual(adapter.token, "test_token")
        self.assertIsNone(adapter._pro)
        self.assertEqual(adapter._min_request_interval, 0.05)

    @patch('src.core.data.adapters.tushare_adapter.ts')
    def test_get_pro_lazy_loading(self, mock_ts):
        """测试懒加载机制"""
        mock_pro = Mock()
        mock_ts.pro_api.return_value = mock_pro

        # 第一次调用应该初始化
        pro = self.adapter._get_pro()
        self.assertEqual(pro, mock_pro)
        mock_ts.pro_api.assert_called_once_with(self.test_token)

        # 第二次调用应该返回缓存实例
        pro2 = self.adapter._get_pro()
        self.assertEqual(pro2, mock_pro)
        mock_ts.pro_api.assert_called_once()  # 没有再次调用

    @patch('src.core.data.adapters.tushare_adapter.ts')
    def test_get_pro_import_error(self, mock_ts):
        """测试tushare库未导入的情况"""
        mock_ts.side_effect = ImportError("No module named 'tushare'")

        with self.assertRaises(TushareAdapterError):
            self.adapter._get_pro()

    @patch('src.core.data.adapters.tushare_adapter.ts')
    def test_get_pro_init_error(self, mock_ts):
        """测试tushare初始化失败的情况"""
        mock_ts.pro_api.side_effect = Exception("Initialization failed")

        with self.assertRaises(TushareAdapterError):
            self.adapter._get_pro()

    @patch('src.core.data.adapters.tushare_adapter.time')
    def test_rate_limit(self, mock_time):
        """测试频率限制"""
        # 模拟时间间隔
        mock_time.time.side_effect = [0, 0.01]  # 当前时间，上一次时间

        # 第一次调用不应该睡眠
        self.adapter._rate_limit()
        mock_time.sleep.assert_not_called()

        # 模拟时间间隔过小的情况
        mock_time.time.side_effect = [0.02, 0.01]  # 当前时间，上一次时间
        self.adapter._rate_limit()
        mock_time.sleep.assert_called_once()

    @patch.object(TushareAdapter, '_get_pro')
    @patch.object(TushareAdapter, '_rate_limit')
    def test_get_stock_basic_success(self, mock_rate_limit, mock_get_pro):
        """测试成功获取股票基本信息"""
        # 模拟tushare返回数据
        mock_pro = Mock()
        mock_df = pd.DataFrame({
            'ts_code': ['000001.SZ', '000002.SZ'],
            'symbol': ['000001', '000002'],
            'name': ['平安银行', '万科A'],
            'industry': ['银行', '房地产']
        })
        mock_pro.stock_basic.return_value = mock_df
        mock_get_pro.return_value = mock_pro

        # 调用方法
        result = self.adapter.get_stock_basic()

        # 验证
        mock_rate_limit.assert_called_once()
        mock_pro.stock_basic.assert_called_once()
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(len(result), 2)

    @patch.object(TushareAdapter, '_get_pro')
    @patch.object(TushareAdapter, '_rate_limit')
    def test_get_stock_basic_with_params(self, mock_rate_limit, mock_get_pro):
        """测试带参数的股票基本信息获取"""
        mock_pro = Mock()
        mock_df = pd.DataFrame({'ts_code': ['600000.SH']})
        mock_pro.stock_basic.return_value = mock_df
        mock_get_pro.return_value = mock_pro

        fields = ['ts_code', 'symbol', 'name']
        result = self.adapter.get_stock_basic(exchange='SSE', list_status='L', fields=fields)

        mock_pro.stock_basic.assert_called_once_with(
            exchange='SSE',
            list_status='L',
            fields='ts_code,symbol,name'
        )

    @patch.object(TushareAdapter, '_get_pro')
    @patch.object(TushareAdapter, '_rate_limit')
    def test_get_stock_basic_exception(self, mock_rate_limit, mock_get_pro):
        """测试获取股票基本信息时发生异常"""
        mock_pro = Mock()
        mock_pro.stock_basic.side_effect = Exception("API Error")
        mock_get_pro.return_value = mock_pro

        with self.assertRaises(TushareAdapterError):
            self.adapter.get_stock_basic()

    @patch.object(TushareAdapter, '_get_pro')
    @patch.object(TushareAdapter, '_rate_limit')
    def test_get_daily_data_success(self, mock_rate_limit, mock_get_pro):
        """测试成功获取日线数据"""
        mock_pro = Mock()
        mock_df = pd.DataFrame({
            'ts_code': ['000001.SZ'],
            'trade_date': ['20240101'],
            'open': [10.0],
            'close': [11.0]
        })
        mock_pro.daily.return_value = mock_df
        mock_get_pro.return_value = mock_pro

        result = self.adapter.get_daily_data('000001.SZ', '20240101', '20240102')

        mock_rate_limit.assert_called_once()
        mock_pro.daily.assert_called_once_with(
            ts_code='000001.SZ',
            start_date='20240101',
            end_date='20240102'
        )
        self.assertIsInstance(result, pd.DataFrame)

    @patch.object(TushareAdapter, '_get_pro')
    @patch.object(TushareAdapter, '_rate_limit')
    def test_get_daily_data_with_fields(self, mock_rate_limit, mock_get_pro):
        """测试带字段过滤的日线数据获取"""
        mock_pro = Mock()
        mock_df = pd.DataFrame({
            'ts_code': ['000001.SZ'],
            'trade_date': ['20240101'],
            'open': [10.0],
            'close': [11.0],
            'high': [12.0]  # 额外字段
        })
        mock_pro.daily.return_value = mock_df
        mock_get_pro.return_value = mock_pro

        fields = ['ts_code', 'trade_date', 'open', 'close']
        result = self.adapter.get_daily_data('000001.SZ', '20240101', '20240102', fields=fields)

        # 验证字段过滤
        self.assertEqual(list(result.columns), fields)

    @patch.object(TushareAdapter, '_get_pro')
    @patch.object(TushareAdapter, '_rate_limit')
    def test_get_realtime_quote_success(self, mock_rate_limit, mock_get_pro):
        """测试成功获取实时行情"""
        mock_pro = Mock()
        mock_df = pd.DataFrame({
            'ts_code': ['000001.SZ', '000002.SZ'],
            'price': [10.5, 20.3],
            'change': [0.5, 0.3]
        })
        mock_pro.realtime_quote.return_value = mock_df
        mock_get_pro.return_value = mock_pro

        ts_codes = ['000001.SZ', '000002.SZ']
        result = self.adapter.get_realtime_quote(ts_codes)

        mock_rate_limit.assert_called_once()
        mock_pro.realtime_quote.assert_called_once_with(ts_code='000001.SZ,000002.SZ')
        self.assertIsInstance(result, pd.DataFrame)

    @patch.object(TushareAdapter, '_get_pro')
    @patch.object(TushareAdapter, '_rate_limit')
    def test_get_financial_data_success(self, mock_rate_limit, mock_get_pro):
        """测试成功获取财务数据"""
        mock_pro = Mock()
        mock_df = pd.DataFrame({
            'ts_code': ['000001.SZ'],
            'end_date': ['20231231'],
            'total_revenue': [1000000],
            'net_profit': [100000]
        })
        mock_pro.fina_indicator.return_value = mock_df
        mock_get_pro.return_value = mock_pro

        result = self.adapter.get_financial_data('000001.SZ', '20230101', '20231231')

        mock_rate_limit.assert_called_once()
        mock_pro.fina_indicator.assert_called_once_with(
            ts_code='000001.SZ',
            start_date='20230101',
            end_date='20231231',
            report_type='1'
        )
        self.assertIsInstance(result, pd.DataFrame)

    @patch.object(TushareAdapter, '_get_pro')
    @patch.object(TushareAdapter, '_rate_limit')
    def test_get_index_basic_success(self, mock_rate_limit, mock_get_pro):
        """测试成功获取指数基本信息"""
        mock_pro = Mock()
        mock_df = pd.DataFrame({
            'ts_code': ['000001.SH'],
            'name': ['上证指数'],
            'market': ['SSE']
        })
        mock_pro.index_basic.return_value = mock_df
        mock_get_pro.return_value = mock_pro

        result = self.adapter.get_index_basic(exchange='SSE')

        mock_rate_limit.assert_called_once()
        mock_pro.index_basic.assert_called_once_with(exchange='SSE', market='')
        self.assertIsInstance(result, pd.DataFrame)

    @patch.object(TushareAdapter, '_get_pro')
    @patch.object(TushareAdapter, '_rate_limit')
    def test_get_index_daily_success(self, mock_rate_limit, mock_get_pro):
        """测试成功获取指数日线数据"""
        mock_pro = Mock()
        mock_df = pd.DataFrame({
            'ts_code': ['000001.SH'],
            'trade_date': ['20240101'],
            'close': [3000.0]
        })
        mock_pro.index_daily.return_value = mock_df
        mock_get_pro.return_value = mock_pro

        result = self.adapter.get_index_daily('000001.SH', '20240101', '20240102')

        mock_rate_limit.assert_called_once()
        mock_pro.index_daily.assert_called_once_with(
            ts_code='000001.SH',
            start_date='20240101',
            end_date='20240102'
        )
        self.assertIsInstance(result, pd.DataFrame)

    @patch.object(TushareAdapter, 'get_stock_basic')
    def test_connection_success(self, mock_get_stock_basic):
        """测试连接成功"""
        mock_get_stock_basic.return_value = pd.DataFrame({'ts_code': ['000001.SZ']})

        result = self.adapter.test_connection()

        self.assertTrue(result)
        mock_get_stock_basic.assert_called_once()

    @patch.object(TushareAdapter, 'get_stock_basic')
    def test_connection_failure(self, mock_get_stock_basic):
        """测试连接失败"""
        mock_get_stock_basic.side_effect = Exception("Connection failed")

        result = self.adapter.test_connection()

        self.assertFalse(result)


if __name__ == '__main__':
    unittest.main()