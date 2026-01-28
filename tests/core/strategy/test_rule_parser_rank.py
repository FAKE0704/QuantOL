"""RANK函数测试模块"""
import os
import sys
import pytest
import pandas as pd
import numpy as np
from datetime import datetime

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, project_root)

from src.core.strategy.indicators import IndicatorService
from src.core.strategy.rule_parser import RuleParser


@pytest.fixture
def sample_data_dict():
    """创建测试用多标的样本数据"""
    dates = pd.date_range('2024-01-01', periods=50, freq='D')

    data_dict = {}
    # 创建5只股票的测试数据，按价格排序
    test_prices = {
        'STOCK_A': [150] * 50,  # 最高价
        'STOCK_B': [120] * 50,
        'STOCK_C': [100] * 50,
        'STOCK_D': [80] * 50,
        'STOCK_E': [50] * 50   # 最低价
    }

    for symbol, prices in test_prices.items():
        data = pd.DataFrame({
            'date': [d.strftime('%Y-%m-%d') for d in dates],
            'close': prices,
            'high': [p * 1.02 for p in prices],
            'low': [p * 0.98 for p in prices],
            'volume': np.random.randint(1000000, 10000000, 50),
            'open': [p * 1.01 for p in prices]
        })
        data['combined_time'] = pd.to_datetime(data['date'], format='%Y-%m-%d')
        data_dict[symbol] = data

    return data_dict


@pytest.fixture
def cross_sectional_context(sample_data_dict):
    """创建横截面上下文"""
    return {
        'data_dict': sample_data_dict,
        'current_symbol': 'STOCK_C',  # 默认测试STOCK_C
        'current_timestamp': pd.Timestamp('2024-01-10')
    }


@pytest.fixture
def indicator_service():
    """创建指标服务"""
    return IndicatorService()


@pytest.fixture
def parser_with_context(sample_data_dict, indicator_service):
    """创建带横截面上下文的解析器工厂函数"""
    def _create_parser(symbol='STOCK_C', timestamp=pd.Timestamp('2024-01-10')):
        data = sample_data_dict[symbol].copy()
        context = {
            'data_dict': sample_data_dict,
            'current_symbol': symbol,
            'current_timestamp': timestamp
        }
        return RuleParser(data, indicator_service, None, context)
    return _create_parser


class TestRankFunction:
    """测试RANK函数"""

    def test_rank_basic(self, parser_with_context):
        """测试基本排名功能"""
        parser = parser_with_context('STOCK_C')  # STOCK_C价格=100，应该排名第3
        parser.current_index = 10

        result = parser.parse("RANK(close)", mode='factor')
        assert result == 3  # STOCK_A=150(1), STOCK_B=120(2), STOCK_C=100(3), STOCK_D=80(4), STOCK_E=50(5)

    def test_rank_highest(self, parser_with_context):
        """测试最高价排名"""
        parser = parser_with_context('STOCK_A')  # STOCK_A价格=150，应该排名第1
        parser.current_index = 10

        result = parser.parse("RANK(close)", mode='factor')
        assert result == 1

    def test_rank_lowest(self, parser_with_context):
        """测试最低价排名"""
        parser = parser_with_context('STOCK_E')  # STOCK_E价格=50，应该排名第5
        parser.current_index = 10

        result = parser.parse("RANK(close)", mode='factor')
        assert result == 5

    def test_rank_volume_field(self, parser_with_context):
        """测试成交量排名"""
        parser = parser_with_context('STOCK_C')
        parser.current_index = 10

        result = parser.parse("RANK(volume)", mode='factor')
        assert isinstance(result, int)
        assert 1 <= result <= 5  # 成交量是随机的，但排名应该在1-5之间

    def test_rank_no_context(self, indicator_service):
        """测试无横截面上下文时返回0"""
        data = pd.DataFrame({'close': [100], 'volume': [1000]})
        parser = RuleParser(data, indicator_service, None, None)
        parser.current_index = 0

        result = parser.parse("RANK(close)", mode='factor')
        assert result == 0  # 无上下文时返回0

    def test_rank_empty_data_dict(self, indicator_service):
        """测试空data_dict时返回0"""
        data = pd.DataFrame({'close': [100], 'volume': [1000]})
        context = {
            'data_dict': {},  # 空字典
            'current_symbol': 'TEST',
            'current_timestamp': pd.Timestamp('2024-01-01')
        }
        parser = RuleParser(data, indicator_service, None, context)
        parser.current_index = 0

        result = parser.parse("RANK(close)", mode='factor')
        assert result == 0

    def test_rank_in_rule_expression(self, parser_with_context):
        """测试RANK在规则表达式中的使用"""
        parser = parser_with_context('STOCK_A')  # STOCK_A排名第1
        parser.current_index = 10

        # 测试 RANK(close) <= 2 (STOCK_A排名为1，应该返回True)
        result = parser.parse("RANK(close) <= 2", mode='rule')
        assert result is True

    def test_rank_with_ref(self, parser_with_context):
        """测试RANK与REF组合使用"""
        parser = parser_with_context('STOCK_A')
        parser.current_index = 10

        # 由于价格是固定的，REF(RANK(close), 5) 应该和 RANK(close) 相同
        current_rank = parser.parse("RANK(close)", mode='factor')
        ref_rank = parser.parse("REF(RANK(close), 5)", mode='factor')

        assert current_rank == ref_rank

    def test_rank_comparison_expression(self, parser_with_context):
        """测试RANK在比较表达式中的使用"""
        parser = parser_with_context('STOCK_C')  # 排名第3
        parser.current_index = 10

        # RANK(close) > 2 应该为True (排名3 > 2)
        result = parser.parse("RANK(close) > 2", mode='rule')
        assert result is True

        # RANK(close) < 3 应该为False (排名3 不小于 3)
        result = parser.parse("RANK(close) < 3", mode='rule')
        assert result is False

    def test_rank_with_and_condition(self, parser_with_context):
        """测试RANK与AND条件组合"""
        parser = parser_with_context('STOCK_C')
        parser.current_index = 10

        # RANK(close) >= 3 and close > 90 (Python使用小写and)
        result = parser.parse("RANK(close) >= 3 and close > 90", mode='rule')
        assert result is True  # STOCK_C排名3且价格100

    def test_rank_all_symbols_at_different_index(self, parser_with_context):
        """测试在不同索引位置所有股票的排名"""
        # 在索引0处测试
        parser = parser_with_context('STOCK_A')
        parser.current_index = 0
        assert parser.parse("RANK(close)", mode='factor') == 1

        parser = parser_with_context('STOCK_B')
        parser.current_index = 0
        assert parser.parse("RANK(close)", mode='factor') == 2

        # 在索引25处测试
        parser = parser_with_context('STOCK_C')
        parser.current_index = 25
        assert parser.parse("RANK(close)", mode='factor') == 3

        # 在索引49处测试
        parser = parser_with_context('STOCK_D')
        parser.current_index = 49
        assert parser.parse("RANK(close)", mode='factor') == 4

        parser = parser_with_context('STOCK_E')
        parser.current_index = 49
        assert parser.parse("RANK(close)", mode='factor') == 5


class TestRankEdgeCases:
    """测试RANK函数边界情况"""

    def test_rank_with_nan_values(self, sample_data_dict, indicator_service):
        """测试包含NaN值时的排名"""
        # 修改数据使其中一个股票的价格为NaN
        sample_data_dict['STOCK_C'].loc[10, 'close'] = np.nan

        context = {
            'data_dict': sample_data_dict,
            'current_symbol': 'STOCK_A',
            'current_timestamp': pd.Timestamp('2024-01-10')
        }
        data = sample_data_dict['STOCK_A'].copy()
        parser = RuleParser(data, indicator_service, None, context)
        parser.current_index = 10

        result = parser.parse("RANK(close)", mode='factor')
        # STOCK_C有NaN，所以只有4个有效股票，STOCK_A仍然应该是第1
        assert result == 1

    def test_rank_symbol_not_in_data_dict(self, indicator_service):
        """测试当前symbol不在data_dict中时返回0"""
        data = pd.DataFrame({'close': [100], 'volume': [1000]})
        context = {
            'data_dict': {'OTHER': pd.DataFrame({'close': [50]})},
            'current_symbol': 'MISSING',  # 不在data_dict中
            'current_timestamp': pd.Timestamp('2024-01-01')
        }
        parser = RuleParser(data, indicator_service, None, context)
        parser.current_index = 0

        result = parser.parse("RANK(close)", mode='factor')
        assert result == 0  # symbol不在data_dict中，返回0

    def test_rank_invalid_index(self, sample_data_dict, indicator_service):
        """测试索引超出范围时返回0"""
        context = {
            'data_dict': sample_data_dict,
            'current_symbol': 'STOCK_A',
            'current_timestamp': pd.Timestamp('2024-01-01')
        }
        data = sample_data_dict['STOCK_A'].copy()
        parser = RuleParser(data, indicator_service, None, context)
        parser.current_index = 1000  # 超出范围

        result = parser.parse("RANK(close)", mode='factor')
        # 应该返回0，因为无法获取当前symbol的值
        assert result == 0
