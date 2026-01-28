"""基于横截面排名的策略测试"""
import os
import sys
import pytest
import pandas as pd
import numpy as np
from datetime import datetime
from unittest.mock import Mock

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
sys.path.insert(0, project_root)

from src.core.strategy.indicators import IndicatorService
from src.core.strategy.cross_sectional.ranking_config import RankingConfig
from src.core.strategy.cross_sectional.ranking_service import CrossSectionalRankingService
from src.core.strategy.cross_sectional.ranking_strategy import RankingBasedStrategy


@pytest.fixture
def sample_data_dict():
    """创建测试用多标的样本数据"""
    dates = pd.date_range('2024-01-01', periods=100, freq='D')

    data_dict = {}
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


@pytest.fixture
def mock_portfolio_manager():
    """创建模拟投资组合管理器"""
    manager = Mock()
    manager.get_position = Mock(return_value=None)
    manager.get_all_positions = Mock(return_value={})
    manager.get_portfolio_value = Mock(return_value=1000000.0)
    return manager


@pytest.fixture
def ranking_strategy(sample_data_dict, ranking_service, mock_portfolio_manager):
    """创建基于排名的策略"""
    return RankingBasedStrategy(
        data_dict=sample_data_dict,
        name="test_ranking_strategy",
        ranking_service=ranking_service,
        portfolio_manager=mock_portfolio_manager,
        indicator_service=ranking_service.indicator_service
    )


class TestRankingBasedStrategy:
    """测试基于横截面排名的策略"""

    def test_init(self, sample_data_dict, ranking_service, mock_portfolio_manager):
        """测试策略初始化"""
        strategy = RankingBasedStrategy(
            data_dict=sample_data_dict,
            name="test_strategy",
            ranking_service=ranking_service,
            portfolio_manager=mock_portfolio_manager
        )

        assert strategy.name == "test_strategy"
        assert strategy.ranking_service == ranking_service
        assert strategy.portfolio_manager == mock_portfolio_manager
        assert len(strategy.current_positions) == 0
        assert len(strategy.target_positions) == 0

    def test_should_rebalance_first_time(self, ranking_strategy):
        """测试首次再平衡判断"""
        timestamp = pd.Timestamp('2024-01-01')
        assert ranking_strategy.should_rebalance(timestamp) == True

    def test_should_rebalance_monthly(self, ranking_strategy):
        """测试每月再平衡判断"""
        # 设置上次再平衡日期
        ranking_strategy.last_rebalance_date = pd.Timestamp('2024-01-01')

        # 同一天不应再次触发
        assert ranking_strategy.should_rebalance(pd.Timestamp('2024-01-01')) == False

        # 2月1号应该触发
        assert ranking_strategy.should_rebalance(pd.Timestamp('2024-02-01')) == True

    def test_should_rebalance_not_on_rebalance_day(self, ranking_strategy):
        """测试非再平衡日判断"""
        ranking_strategy.last_rebalance_date = pd.Timestamp('2024-01-01')
        assert ranking_strategy.should_rebalance(pd.Timestamp('2024-01-15')) == False

    def test_calculate_signals(self, ranking_strategy, sample_data_dict):
        """测试信号计算"""
        timestamp = pd.Timestamp('2024-01-01')
        current_prices = {
            'AAPL': 105.0,
            'MSFT': 110.0,
            'GOOGL': 108.0,
            'AMZN': 95.0,
            'TSLA': 102.0
        }

        signals = ranking_strategy.calculate_signals(timestamp, current_prices)

        # 验证信号类型
        assert all(hasattr(s, 'signal_type') for s in signals)

        # 验证目标持仓已更新
        assert len(ranking_strategy.target_positions) > 0

        # 验证最后排名已记录
        assert ranking_strategy.last_ranking is not None

    def test_calculate_signals_no_rebalance_needed(self, ranking_strategy):
        """测试不需要再平衡时的信号计算"""
        # 设置上次再平衡日期为最近
        ranking_strategy.last_rebalance_date = pd.Timestamp('2024-01-01')

        timestamp = pd.Timestamp('2024-01-15')
        current_prices = {'AAPL': 105.0}

        signals = ranking_strategy.calculate_signals(timestamp, current_prices)

        # 不应生成信号
        assert len(signals) == 0

    def test_get_current_target_positions(self, ranking_strategy):
        """测试获取目标持仓"""
        ranking_strategy.target_positions = {'AAPL', 'MSFT', 'GOOGL'}
        target = ranking_strategy.get_current_target_positions()

        assert target == {'AAPL', 'MSFT', 'GOOGL'}

    def test_get_current_positions(self, ranking_strategy, mock_portfolio_manager):
        """测试获取当前持仓"""
        # 设置模拟持仓
        mock_position = Mock()
        mock_position.quantity = 100
        mock_portfolio_manager.get_all_positions = Mock(
            return_value={'AAPL': mock_position, 'MSFT': mock_position}
        )

        positions = ranking_strategy.get_current_positions()

        assert 'AAPL' in positions
        assert 'MSFT' in positions

    def test_get_last_ranking(self, ranking_strategy, sample_data_dict):
        """测试获取最后排名结果"""
        timestamp = pd.Timestamp('2024-01-01')
        current_prices = {
            'AAPL': 105.0,
            'MSFT': 110.0,
        }

        ranking_strategy.calculate_signals(timestamp, current_prices)
        last_ranking = ranking_strategy.get_last_ranking()

        assert last_ranking is not None
        assert isinstance(last_ranking, pd.DataFrame)

    def test_create_buy_signal(self, ranking_strategy):
        """测试创建买入信号"""
        from src.event_bus.event_types import StrategySignalEvent
        from src.core.strategy.signal_types import SignalType

        signal = ranking_strategy._create_buy_signal(
            symbol='AAPL',
            price=105.0,
            timestamp=pd.Timestamp('2024-01-01'),
            weight=0.1
        )

        assert signal.symbol == 'AAPL'
        assert signal.price == 105.0
        assert signal.signal_type == SignalType.REBALANCE
        assert signal.position_percent == 0.1

    def test_create_sell_signal(self, ranking_strategy, mock_portfolio_manager):
        """测试创建卖出信号"""
        from src.core.strategy.signal_types import SignalType

        # 设置模拟持仓
        mock_position = Mock()
        mock_position.quantity = 100
        mock_portfolio_manager.get_position = Mock(return_value=mock_position)

        signal = ranking_strategy._create_sell_signal(
            symbol='AAPL',
            price=105.0,
            timestamp=pd.Timestamp('2024-01-01')
        )

        assert signal.symbol == 'AAPL'
        assert signal.price == 105.0
        assert signal.signal_type == SignalType.CLOSE
        assert signal.quantity == 100

    def test_update_current_positions(self, ranking_strategy, mock_portfolio_manager):
        """测试更新当前持仓集合"""
        # 设置模拟持仓
        mock_position1 = Mock()
        mock_position1.quantity = 100
        mock_position2 = Mock()
        mock_position2.quantity = 200
        mock_position3 = Mock()
        mock_position3.quantity = 0  # 零持仓

        mock_portfolio_manager.get_all_positions = Mock(
            return_value={
                'AAPL': mock_position1,
                'MSFT': mock_position2,
                'GOOGL': mock_position3
            }
        )

        ranking_strategy._update_current_positions()

        assert 'AAPL' in ranking_strategy.current_positions
        assert 'MSFT' in ranking_strategy.current_positions
        assert 'GOOGL' not in ranking_strategy.current_positions  # 零持仓

    def test_handle_event(self, ranking_strategy):
        """测试事件处理（基类方法）"""
        # 基于排名的策略不需要响应定时事件
        mock_engine = Mock()
        mock_event = Mock()

        ranking_strategy.handle_event(mock_engine, mock_event)
        # 不应抛出异常

    def test_calculate_signals_with_existing_positions(self, ranking_strategy, mock_portfolio_manager):
        """测试有现有持仓时的信号计算"""
        # 设置当前持仓
        mock_position = Mock()
        mock_position.quantity = 100
        mock_portfolio_manager.get_all_positions = Mock(
            return_value={'AAPL': mock_position}
        )
        ranking_strategy.current_positions = {'AAPL'}

        timestamp = pd.Timestamp('2024-01-01')
        current_prices = {
            'AAPL': 90.0,  # 价格较低，可能不在目标名单中
            'MSFT': 110.0,
            'GOOGL': 108.0,
            'AMZN': 95.0,
            'TSLA': 102.0
        }

        signals = ranking_strategy.calculate_signals(timestamp, current_prices)

        # 应该生成信号（买入和/或卖出）
        # 具体信号数量取决于排名结果
        assert isinstance(signals, list)
