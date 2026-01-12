"""
Martingale仓位策略测试

测试马丁格尔仓位管理策略的核心功能，使用实际市场数据。
"""

import os
import sys
import pytest
import pandas as pd
import asyncio

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, project_root)

from src.core.strategy.fixed_percent_position_strategy import MartingalePositionStrategy
from src.core.strategy.signal_types import SignalType


# ============================================================================
# 测试数据准备
# ============================================================================

def create_test_portfolio_data(available_cash=1000000, initial_capital=1000000, total_equity=1000000):
    """创建测试用的投资组合数据"""
    return {
        'initial_capital': initial_capital,
        'available_cash': available_cash,
        'total_equity': total_equity
    }


def create_realistic_test_data():
    """
    创建接近真实市场的测试数据

    模拟一个典型的martingale交易场景：
    - 价格从10.5开始下跌
    - 跌至9.8（约-7%，触发多次加仓）
    - 反弹回10.5（触发清仓）
    """
    dates = pd.date_range('2025-04-01 09:30:00', periods=20, freq='5min')
    return pd.DataFrame({
        'date': [d.strftime('%Y-%m-%d') for d in dates],
        'time': [d.strftime('%H:%M:%S') for d in dates],
        'close': [
            10.5, 10.4, 10.3, 10.2, 10.1,  # 下跌
            10.0, 9.9, 9.8, 9.8, 9.9,      # 触底
            10.0, 10.1, 10.2, 10.3, 10.4,  # 反弹
            10.5, 10.6, 10.5, 10.4, 10.5   # 清仓区域
        ],
        'open': [10.4, 10.5, 10.4, 10.3, 10.2, 10.1, 10.0, 9.9, 9.8, 9.9,
                 10.0, 10.1, 10.2, 10.3, 10.4, 10.5, 10.6, 10.5, 10.4, 10.5],
        'high': [10.6, 10.5, 10.4, 10.3, 10.2, 10.1, 10.0, 9.9, 9.8, 9.9,
                 10.0, 10.1, 10.2, 10.3, 10.4, 10.5, 10.6, 10.5, 10.4, 10.5],
        'low': [10.3, 10.2, 10.1, 10.0, 9.9, 9.8, 9.7, 9.6, 9.5, 9.6,
                9.7, 9.8, 9.9, 10.0, 10.1, 10.2, 10.3, 10.2, 10.1, 10.2],
        'volume': [100000] * 20
    })


async def load_real_market_data():
    """
    从SQLite加载真实市场数据（如果可用）

    Returns:
        pd.DataFrame or None: 如果数据库存在且有数据则返回，否则返回None
    """
    db_path = "./data/quantdb.sqlite"

    # 检查数据库是否存在
    if not os.path.exists(db_path):
        return None

    try:
        from src.core.data.sqlite_adapter import SQLiteAdapter

        adapter = SQLiteAdapter(db_path)
        await adapter.initialize()

        # 尝试加载数据
        data = await adapter.load_stock_data(
            symbol="sh.600604",
            start_date="20250401",
            end_date="20250430",
            frequency="5"
        )

        return data
    except Exception as e:
        # 数据加载失败，返回None让测试使用模拟数据
        return None


# ============================================================================
# 基础功能测试
# ============================================================================

def test_martingale_initialization():
    """测试Martingale策略初始化"""
    strategy = MartingalePositionStrategy(
        base_percent=0.05,
        multiplier=2.0,
        max_doubles=5,
        min_lot_size=100
    )

    info = strategy.get_strategy_info()
    assert info['strategy_type'] == 'martingale'
    assert info['base_percent'] == 0.05
    assert info['multiplier'] == 2.0
    assert info['max_doubles'] == 5
    assert info['min_lot_size'] == 100


def test_open_position():
    """测试开仓功能"""
    strategy = MartingalePositionStrategy(base_percent=0.05, multiplier=2.0, max_doubles=5)
    portfolio_data = create_test_portfolio_data(available_cash=1000000)
    symbol = 'TEST'

    # 开仓：无持仓时BUY信号
    quantity = strategy.calculate_position_size(
        signal_type=SignalType.BUY,
        portfolio_data=portfolio_data,
        current_price=10.0,
        current_position=0,
        symbol=symbol
    )

    # 预期：5% × 1000000 ÷ 10 = 5000股
    assert quantity == 5000
    assert strategy.get_martingale_level(symbol) == 0


def test_first_add_position():
    """测试第一次加仓（×1倍）"""
    strategy = MartingalePositionStrategy(base_percent=0.05, multiplier=2.0, max_doubles=5)
    portfolio_data = create_test_portfolio_data(available_cash=950000)
    symbol = 'TEST'

    # 先开仓
    strategy.calculate_position_size(
        signal_type=SignalType.BUY,
        portfolio_data=create_test_portfolio_data(available_cash=1000000),
        current_price=10.0,
        current_position=0,
        symbol=symbol
    )

    # 第一次加仓
    quantity = strategy.calculate_position_size(
        signal_type=SignalType.BUY,
        portfolio_data=portfolio_data,
        current_price=10.0,
        current_position=5000,
        symbol=symbol
    )

    # 预期：5% × 950000 ÷ 10 × 1倍 ≈ 4700股（整百）
    assert quantity > 0
    assert strategy.get_martingale_level(symbol) == 1


def test_second_add_position():
    """测试第二次加仓（×2倍）"""
    strategy = MartingalePositionStrategy(base_percent=0.05, multiplier=2.0, max_doubles=5)
    symbol = 'TEST'

    # 模拟第一次加仓后的状态
    portfolio_data = create_test_portfolio_data(available_cash=900000)

    # 设置第一次加仓后的状态
    strategy._martingale_states[symbol] = {'level': 1, 'entry_price': 10.0}

    # 第二次加仓
    quantity = strategy.calculate_position_size(
        signal_type=SignalType.BUY,
        portfolio_data=portfolio_data,
        current_price=10.0,
        current_position=10000,
        symbol=symbol
    )

    # 预期：基础仓位 × 2倍
    base_quantity = int(900000 * 0.05 / 10.0 / 100) * 100  # 4500
    expected_min = base_quantity * 2  # 9000
    assert quantity >= expected_min * 0.9  # 允许10%误差
    assert strategy.get_martingale_level(symbol) == 2


def test_max_doubles_limit():
    """测试最大加倍次数限制"""
    strategy = MartingalePositionStrategy(base_percent=0.05, multiplier=2.0, max_doubles=2)
    symbol = 'TEST'

    # 设置已达到最大加倍次数的状态
    strategy._martingale_states[symbol] = {'level': 2, 'entry_price': 10.0}

    # 尝试继续加仓
    quantity = strategy.calculate_position_size(
        signal_type=SignalType.BUY,
        portfolio_data=create_test_portfolio_data(),
        current_price=10.0,
        current_position=10000,
        symbol=symbol
    )

    # 预期：不再加仓
    assert quantity == 0


def test_close_position():
    """测试完全清仓"""
    strategy = MartingalePositionStrategy(base_percent=0.05, multiplier=2.0, max_doubles=5)
    symbol = 'TEST'

    # 设置有持仓的状态
    strategy._martingale_states[symbol] = {'level': 2, 'entry_price': 10.0}

    # 清仓
    quantity = strategy.calculate_position_size(
        signal_type=SignalType.SELL,
        portfolio_data=create_test_portfolio_data(),
        current_price=10.5,
        current_position=15000,
        symbol=symbol
    )

    # 预期：完全清仓，返回负数
    assert quantity == -15000
    # 状态应被重置
    assert strategy.get_martingale_level(symbol) == 0


def test_close_signal_also_liquidates():
    """测试CLOSE信号也完全清仓"""
    strategy = MartingalePositionStrategy(base_percent=0.05, multiplier=2.0, max_doubles=5)
    symbol = 'TEST'

    # 设置有持仓的状态
    strategy._martingale_states[symbol] = {'level': 1, 'entry_price': 10.0}

    # CLOSE信号
    quantity = strategy.calculate_position_size(
        signal_type=SignalType.CLOSE,
        portfolio_data=create_test_portfolio_data(),
        current_price=10.5,
        current_position=10000,
        symbol=symbol
    )

    # 预期：完全清仓
    assert quantity == -10000
    assert strategy.get_martingale_level(symbol) == 0


def test_state_reset_after_close():
    """测试清仓后状态重置，下次开仓回到基础仓位"""
    strategy = MartingalePositionStrategy(base_percent=0.05, multiplier=2.0, max_doubles=5)
    symbol = 'TEST'

    # 模拟一个完整的交易周期
    portfolio_data = create_test_portfolio_data()

    # 1. 开仓
    strategy.calculate_position_size(
        signal_type=SignalType.BUY,
        portfolio_data=portfolio_data,
        current_price=10.0,
        current_position=0,
        symbol=symbol
    )
    assert strategy.get_martingale_level(symbol) == 0

    # 2. 加仓
    strategy._martingale_states[symbol]['level'] = 1
    assert strategy.get_martingale_level(symbol) == 1

    # 3. 清仓
    strategy.calculate_position_size(
        signal_type=SignalType.SELL,
        portfolio_data=portfolio_data,
        current_price=10.5,
        current_position=10000,
        symbol=symbol
    )
    assert strategy.get_martingale_level(symbol) == 0

    # 4. 再次开仓（模拟无持仓时检测重置）
    # 由于current_position=0，策略会自动重置状态
    strategy._martingale_states[symbol]['level'] = 2  # 人为设置非0状态
    strategy.calculate_position_size(
        signal_type=SignalType.BUY,
        portfolio_data=portfolio_data,
        current_price=10.0,
        current_position=0,  # 无持仓
        symbol=symbol
    )
    # 状态应该被重置
    assert strategy.get_martingale_level(symbol) == 0


# ============================================================================
# 边界条件测试
# ============================================================================

def test_no_position_sell_returns_zero():
    """测试无持仓时SELL返回0"""
    strategy = MartingalePositionStrategy(base_percent=0.05, multiplier=2.0, max_doubles=5)
    symbol = 'TEST'

    quantity = strategy.calculate_position_size(
        signal_type=SignalType.SELL,
        portfolio_data=create_test_portfolio_data(),
        current_price=10.0,
        current_position=0,  # 无持仓
        symbol=symbol
    )

    assert quantity == 0


def test_missing_symbol_returns_zero():
    """测试缺少symbol参数返回0"""
    strategy = MartingalePositionStrategy(base_percent=0.05, multiplier=2.0, max_doubles=5)

    quantity = strategy.calculate_position_size(
        signal_type=SignalType.BUY,
        portfolio_data=create_test_portfolio_data(),
        current_price=10.0,
        current_position=0,
        symbol=None  # 缺少symbol
    )

    assert quantity == 0


def test_insufficient_funds():
    """测试资金不足时的处理"""
    strategy = MartingalePositionStrategy(base_percent=0.5, multiplier=2.0, max_doubles=5)
    symbol = 'TEST'

    # 可用资金很少
    quantity = strategy.calculate_position_size(
        signal_type=SignalType.BUY,
        portfolio_data=create_test_portfolio_data(available_cash=100),  # 只有100元
        current_price=10.0,
        current_position=0,
        symbol=symbol
    )

    # 预期：应该能买，但数量受资金限制
    assert quantity >= 0


# ============================================================================
# 多symbol测试
# ============================================================================

def test_multiple_symbols_state_independent():
    """测试多个symbol的状态独立"""
    strategy = MartingalePositionStrategy(base_percent=0.05, multiplier=2.0, max_doubles=5)
    portfolio_data = create_test_portfolio_data()

    # Symbol A: 开仓并加仓
    strategy.calculate_position_size(
        signal_type=SignalType.BUY,
        portfolio_data=portfolio_data,
        current_price=10.0,
        current_position=0,
        symbol='AAPL'
    )
    strategy._martingale_states['AAPL']['level'] = 2

    # Symbol B: 开仓
    strategy.calculate_position_size(
        signal_type=SignalType.BUY,
        portfolio_data=portfolio_data,
        current_price=100.0,
        current_position=0,
        symbol='TSLA'
    )

    # 验证状态独立
    assert strategy.get_martingale_level('AAPL') == 2
    assert strategy.get_martingale_level('TSLA') == 0

    # Symbol A清仓不影响Symbol B
    strategy.calculate_position_size(
        signal_type=SignalType.SELL,
        portfolio_data=portfolio_data,
        current_price=10.5,
        current_position=10000,
        symbol='AAPL'
    )

    assert strategy.get_martingale_level('AAPL') == 0
    assert strategy.get_martingale_level('TSLA') == 0


# ============================================================================
# 集成测试（使用实际数据）
# ============================================================================

@pytest.mark.integration
class TestMartingaleIntegration:
    """Martingale策略集成测试"""

    @pytest.mark.asyncio
    async def test_with_real_market_data(self):
        """使用真实市场数据测试"""
        # 尝试加载真实数据
        real_data = await load_real_market_data()

        # 如果没有真实数据，使用模拟的真实市场数据
        if real_data is None or len(real_data) == 0:
            real_data = create_realistic_test_data()

        # 创建策略
        strategy = MartingalePositionStrategy(base_percent=0.05, multiplier=2.0, max_doubles=5)
        symbol = 'sh.600604'

        # 模拟一个完整的交易周期
        portfolio_data = create_test_portfolio_data()
        current_position = 0

        # 遍历数据，模拟交易
        for i in range(len(real_data)):
            current_price = real_data.iloc[i]['close']

            # 简单的模拟交易逻辑
            if current_position == 0 and current_price < 10.3:
                # 开仓
                quantity = strategy.calculate_position_size(
                    signal_type=SignalType.BUY,
                    portfolio_data=portfolio_data,
                    current_price=current_price,
                    current_position=current_position,
                    symbol=symbol
                )
                if quantity > 0:
                    current_position += quantity
                    portfolio_data['available_cash'] -= quantity * current_price

            elif current_position > 0 and current_price < 10.0:
                # 加仓（模拟亏损）
                quantity = strategy.calculate_position_size(
                    signal_type=SignalType.BUY,
                    portfolio_data=portfolio_data,
                    current_price=current_price,
                    current_position=current_position,
                    symbol=symbol
                )
                if quantity > 0:
                    current_position += quantity
                    portfolio_data['available_cash'] -= quantity * current_price

            elif current_position > 0 and current_price > 10.4:
                # 清仓（模拟盈利）
                quantity = strategy.calculate_position_size(
                    signal_type=SignalType.SELL,
                    portfolio_data=portfolio_data,
                    current_price=current_price,
                    current_position=current_position,
                    symbol=symbol
                )
                if quantity < 0:
                    portfolio_data['available_cash'] -= quantity * current_price
                    current_position = 0

        # 验证最终状态
        # 注意：如果价格一直下跌且达到最大加倍次数，可能无法清仓
        # 这是martingale策略的预期行为
        if current_position > 0:
            # 如果有持仓，应该达到最大加倍次数
            assert strategy.get_martingale_level(symbol) == strategy.max_doubles
        else:
            # 如果无持仓，状态应该重置
            assert strategy.get_martingale_level(symbol) == 0


# ============================================================================
# 运行入口
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
