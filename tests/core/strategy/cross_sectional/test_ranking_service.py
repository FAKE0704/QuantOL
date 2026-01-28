"""横截面排名服务测试"""
import os
import sys
import pytest
import pandas as pd
import numpy as np
from datetime import datetime

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
sys.path.insert(0, project_root)

from src.core.strategy.indicators import IndicatorService
from src.core.strategy.cross_sectional.ranking_config import RankingConfig
from src.core.strategy.cross_sectional.ranking_service import CrossSectionalRankingService


@pytest.fixture
def sample_data_dict():
    """创建测试用多标的样本数据"""
    dates = pd.date_range('2024-01-01', periods=100, freq='D')

    data_dict = {}
    # 创建5只股票的测试数据
    for i, symbol in enumerate(['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA']):
        np.random.seed(i)
        data = pd.DataFrame({
            'date': [d.strftime('%Y-%m-%d') for d in dates],
            'close': 100 + np.cumsum(np.random.randn(100) * 2),
            'volume': np.random.randint(1000000, 10000000, 100)
        })
        # 添加combined_time列（回测引擎使用）
        data['combined_time'] = pd.to_datetime(data['date'], format='%Y-%m-%d')
        data_dict[symbol] = data

    return data_dict


@pytest.fixture
def ranking_config():
    """创建排名配置"""
    return RankingConfig(
        factor_expression="close",
        ranking_method="descending",
        top_n=3,
        rebalance_frequency="monthly",
        rebalance_day=1
    )


@pytest.fixture
def ranking_service(ranking_config):
    """创建排名服务"""
    indicator_service = IndicatorService()
    return CrossSectionalRankingService(
        indicator_service=indicator_service,
        ranking_config=ranking_config
    )


class TestRankingConfig:
    """测试RankingConfig配置类"""

    def test_default_config(self):
        """测试默认配置创建"""
        config = RankingConfig(factor_expression="RSI(close, 14)")
        assert config.factor_expression == "RSI(close, 14)"
        assert config.ranking_method == "descending"
        assert config.top_n == 10
        assert config.rebalance_frequency == "monthly"

    def test_invalid_ranking_method(self):
        """测试无效的排名方法"""
        with pytest.raises(ValueError, match="ranking_method 必须是"):
            RankingConfig(factor_expression="close", ranking_method="invalid")

    def test_invalid_rebalance_frequency(self):
        """测试无效的再平衡频率"""
        with pytest.raises(ValueError, match="rebalance_frequency 必须是"):
            RankingConfig(factor_expression="close", rebalance_frequency="invalid")

    def test_invalid_top_n(self):
        """测试无效的top_n"""
        with pytest.raises(ValueError, match="top_n 必须大于0"):
            RankingConfig(factor_expression="close", top_n=0)

    def test_invalid_max_position_percent(self):
        """测试无效的最大仓位比例"""
        with pytest.raises(ValueError, match="max_position_percent 必须在0到1之间"):
            RankingConfig(factor_expression="close", max_position_percent=1.5)

    def test_to_dict(self):
        """测试配置转换为字典"""
        config = RankingConfig(factor_expression="close", top_n=5)
        config_dict = config.to_dict()
        assert config_dict['factor_expression'] == "close"
        assert config_dict['top_n'] == 5

    def test_from_dict(self):
        """测试从字典创建配置"""
        config_dict = {
            'factor_expression': 'RSI(close, 14)',
            'ranking_method': 'ascending',
            'top_n': 5
        }
        config = RankingConfig.from_dict(config_dict)
        assert config.factor_expression == 'RSI(close, 14)'
        assert config.ranking_method == 'ascending'
        assert config.top_n == 5


class TestCrossSectionalRankingService:
    """测试横截面排名服务"""

    def test_calculate_cross_sectional_factor(self, ranking_service, sample_data_dict):
        """测试横截面因子计算"""
        timestamp = pd.Timestamp('2024-01-10')
        factor_values = ranking_service.calculate_cross_sectional_factor(
            data_dict=sample_data_dict,
            timestamp=timestamp
        )

        assert isinstance(factor_values, pd.Series)
        assert len(factor_values) == 5
        assert all(symbol in factor_values.index for symbol in ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA'])

    def test_rank_symbols_descending(self, ranking_service, sample_data_dict):
        """测试降序排名"""
        timestamp = pd.Timestamp('2024-01-10')
        factor_values = ranking_service.calculate_cross_sectional_factor(
            data_dict=sample_data_dict,
            timestamp=timestamp
        )

        ranking_df = ranking_service.rank_symbols(factor_values, ascending=False)

        assert 'symbol' in ranking_df.columns
        assert 'factor_value' in ranking_df.columns
        assert 'rank' in ranking_df.columns
        assert len(ranking_df) <= 5  # 可能有NaN值被过滤

    def test_rank_symbols_ascending(self, ranking_service, sample_data_dict):
        """测试升序排名"""
        timestamp = pd.Timestamp('2024-01-10')
        factor_values = ranking_service.calculate_cross_sectional_factor(
            data_dict=sample_data_dict,
            timestamp=timestamp
        )

        ranking_df = ranking_service.rank_symbols(factor_values, ascending=True)

        assert len(ranking_df) <= 5
        # 验证排名是按因子值升序排列的
        if len(ranking_df) > 1:
            assert ranking_df.iloc[0]['factor_value'] <= ranking_df.iloc[1]['factor_value']

    def test_get_selected_symbols(self, ranking_service, sample_data_dict):
        """测试获取选中标的"""
        timestamp = pd.Timestamp('2024-01-10')
        factor_values = ranking_service.calculate_cross_sectional_factor(
            data_dict=sample_data_dict,
            timestamp=timestamp
        )

        ranking_df = ranking_service.rank_symbols(factor_values)
        selected = ranking_service.get_selected_symbols(ranking_df)

        assert len(selected) <= 3  # top_n=3
        assert isinstance(selected, list)

    def test_get_position_weights(self, ranking_service):
        """测试仓位权重分配"""
        selected_symbols = ['AAPL', 'MSFT', 'GOOGL']
        weights = ranking_service.get_position_weights(selected_symbols)

        assert len(weights) == 3
        assert all(symbol in weights for symbol in selected_symbols)
        # 每个标的的权重不应超过最大限制
        assert all(w <= ranking_service.config.max_position_percent for w in weights.values())

    def test_apply_filters_min_price(self):
        """测试价格过滤"""
        # 创建特定价格的测试数据
        dates = pd.date_range('2024-01-01', periods=20, freq='D')
        timestamp = pd.Timestamp('2024-01-10')

        data_dict = {}
        for symbol, close_price in [('AAPL', 100), ('MSFT', 110), ('GOOGL', 105)]:
            data = pd.DataFrame({
                'date': [d.strftime('%Y-%m-%d') for d in dates],
                'close': close_price,  # 固定价格
                'volume': 1000000
            })
            data['combined_time'] = pd.to_datetime(data['date'], format='%Y-%m-%d')
            data_dict[symbol] = data

        config = RankingConfig(
            factor_expression="close",
            min_price=105.0
        )
        indicator_service = IndicatorService()
        service = CrossSectionalRankingService(indicator_service, config)

        factor_values = pd.Series({'AAPL': 100, 'MSFT': 110, 'GOOGL': 105})

        filtered = service.apply_filters(data_dict, timestamp, factor_values)

        # AAPL应该被过滤掉（价格低于105）
        assert pd.isna(filtered['AAPL'])
        # MSFT和GOOGL应该保留（价格>=105）
        assert filtered['MSFT'] == 110
        assert filtered['GOOGL'] == 105

    def test_should_rebalance_daily(self, ranking_service):
        """测试每日再平衡判断"""
        config = RankingConfig(
            factor_expression="close",
            rebalance_frequency="daily"
        )
        service = CrossSectionalRankingService(ranking_service.indicator_service, config)

        timestamp = pd.Timestamp('2024-01-10')
        assert service.should_rebalance(timestamp) == True  # 每天都需要再平衡

    def test_should_rebalance_weekly(self, ranking_service):
        """测试每周再平衡判断"""
        config = RankingConfig(
            factor_expression="close",
            rebalance_frequency="weekly",
            rebalance_day=1  # 周一
        )
        service = CrossSectionalRankingService(ranking_service.indicator_service, config)

        # 周一
        monday = pd.Timestamp('2024-01-08')  # 2024-01-08是周一
        assert service.should_rebalance(monday) == True

        # 周三
        wednesday = pd.Timestamp('2024-01-10')
        assert service.should_rebalance(wednesday) == False

    def test_should_rebalance_monthly(self, ranking_service):
        """测试每月再平衡判断"""
        config = RankingConfig(
            factor_expression="close",
            rebalance_frequency="monthly",
            rebalance_day=1
        )
        service = CrossSectionalRankingService(ranking_service.indicator_service, config)

        # 每月1号
        first_day = pd.Timestamp('2024-01-01')
        assert service.should_rebalance(first_day) == True

        # 月中
        mid_month = pd.Timestamp('2024-01-15')
        assert service.should_rebalance(mid_month) == False

    def test_should_rebalance_cooldown(self, ranking_service):
        """测试再平衡冷却期"""
        config = RankingConfig(
            factor_expression="close",
            rebalance_frequency="weekly",
            rebalance_day=1
        )
        service = CrossSectionalRankingService(ranking_service.indicator_service, config)

        monday1 = pd.Timestamp('2024-01-08')
        monday2 = pd.Timestamp('2024-01-15')

        # 第一次应该触发
        assert service.should_rebalance(monday1) == True

        # 设置上次再平衡日期
        last_rebalance = monday1

        # 7天后应该再次触发
        assert service.should_rebalance(monday2, last_rebalance) == True

        # 3天后不应触发
        wednesday = pd.Timestamp('2024-01-10')
        assert service.should_rebalance(wednesday, last_rebalance) == False
