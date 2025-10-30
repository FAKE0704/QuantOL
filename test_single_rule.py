#!/usr/bin/env python3
"""
单规则快速测试脚本
用于快速测试单个规则表达式的正确性
"""

import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock

# 确保项目根目录在Python路径中
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 模拟Streamlit session_state
class MockSessionState:
    def __init__(self):
        self.db = Mock()
        self.db._loop = Mock()
        self.db.load_stock_data = Mock()
        self.db.load_multiple_stock_data = Mock()
        self.db.get_all_stocks = Mock()

# 创建全局session_state模拟对象
mock_session_state = MockSessionState()

# 在导入前设置模拟的session_state
import streamlit as st
st.session_state = mock_session_state

from src.core.strategy.backtesting import BacktestEngine, BacktestConfig
from src.core.strategy.rule_based_strategy import RuleBasedStrategy
from src.core.strategy.indicators import IndicatorService

def create_test_data(days=100):
    """创建测试数据"""
    np.random.seed(42)
    dates = pd.date_range(start='2024-01-01', periods=days, freq='D')

    # 生成价格数据
    base_price = 100
    closes = [base_price]
    for i in range(1, days):
        change = np.random.normal(0.001, 0.02)
        new_price = closes[-1] * (1 + change)
        closes.append(max(new_price, 1))

    data = []
    for i, (date, close) in enumerate(zip(dates, closes)):
        high = close * (1 + abs(np.random.normal(0, 0.01)))
        low = close * (1 - abs(np.random.normal(0, 0.01)))
        open_price = low + (high - low) * np.random.random()
        volume = int(np.random.normal(1000000, 200000))

        data.append({
            'combined_time': date,
            'open': round(open_price, 2),
            'high': round(high, 2),
            'low': round(low, 2),
            'close': round(close, 2),
            'volume': max(volume, 100000),
            'code': 'test.000001'
        })

    return pd.DataFrame(data)

def test_rule(buy_rule, sell_rule="", open_rule="", close_rule="", days=100):
    """测试单个规则"""
    print(f"🧪 测试规则:")
    print(f"   开仓: {open_rule or '无'}")
    print(f"   清仓: {close_rule or '无'}")
    print(f"   加仓: {buy_rule or '无'}")
    print(f"   平仓: {sell_rule or '无'}")
    print("-" * 50)

    try:
        # 创建测试数据和配置
        data = create_test_data(days)
        config = BacktestConfig(
            start_date='20240101',
            end_date='20240410' if days >= 100 else '20240110',
            target_symbol='test.000001',
            frequency='d',
            initial_capital=100000,
            commission_rate=0.0003,
            strategy_type="自定义规则"
        )

        # 创建回测引擎
        engine = BacktestEngine(config=config, data=data)
        indicator_service = IndicatorService()

        # 注册策略
        strategy = RuleBasedStrategy(
            Data=data,
            name="单规则测试策略",
            indicator_service=indicator_service,
            buy_rule_expr=buy_rule,
            sell_rule_expr=sell_rule,
            open_rule_expr=open_rule,
            close_rule_expr=close_rule,
            portfolio_manager=engine.portfolio_manager
        )
        engine.register_strategy(strategy)

        # 运行回测
        start_date = pd.to_datetime(config.start_date)
        end_date = pd.to_datetime(config.end_date)
        engine.run(start_date, end_date)

        # 获取结果
        results = engine.get_results()
        summary = results.get('summary', {})
        trades = results.get('trades', [])
        debug_data = results.get('debug_data', {})

        # 显示结果
        print(f"✅ 回测完成")
        print(f"   初始资金: {summary.get('initial_capital', 0):,.0f}")
        print(f"   最终资金: {summary.get('final_capital', 0):,.0f}")
        print(f"   总收益率: {summary.get('total_return', 0):.2%}")
        print(f"   最大回撤: {summary.get('max_drawdown', 0):.2%}")
        print(f"   交易次数: {len(trades)}")
        print(f"   胜率: {summary.get('win_rate', 0):.2%}")

        # 调试数据分析
        if debug_data:
            print(f"\n🐛 调试数据分析:")
            for strategy_name, strategy_data in debug_data.items():
                if strategy_data is not None:
                    cols = list(strategy_data.columns)
                    indicator_cols = [c for c in cols if any(func in c for func in ['SMA', 'RSI', 'MACD', 'REF'])]
                    rule_cols = [c for c in cols if c not in ['open', 'high', 'low', 'close', 'volume', 'code', 'combined_time'] and not any(func in c for func in ['SMA', 'RSI', 'MACD', 'REF'])]

                    print(f"   {strategy_name}:")
                    print(f"     - 总列数: {len(cols)}")
                    print(f"     - 指标列: {len(indicator_cols)} ({', '.join(indicator_cols[:3])}{'...' if len(indicator_cols) > 3 else ''})")
                    print(f"     - 规则列: {len(rule_cols)} ({', '.join(rule_cols[:3])}{'...' if len(rule_cols) > 3 else ''})")

        # 显示交易记录
        if trades:
            print(f"\n💱 最近5笔交易:")
            for trade in trades[-5:]:
                print(f"   {trade.get('timestamp', 'N/A')} - {trade.get('direction', 'N/A')} {trade.get('quantity', 0)}股 @ {trade.get('price', 0):.2f}")

        return results

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    """主函数 - 交互式规则测试"""
    print("🎯 单规则快速测试工具")
    print("=" * 50)

    # 预定义的测试规则
    test_rules = [
        {
            'name': '基础SMA策略',
            'buy_rule': 'SMA(close,5) > SMA(close,20)',
            'sell_rule': 'SMA(close,5) < SMA(close,20)'
        },
        {
            'name': 'RSI策略',
            'buy_rule': 'RSI(close,14) < 30',
            'sell_rule': 'RSI(close,14) > 70'
        },
        {
            'name': 'REF函数策略',
            'buy_rule': 'REF(SMA(close,5),1) < SMA(close,5)',
            'sell_rule': 'REF(SMA(close,5),1) > SMA(close,5)'
        }
    ]

    print("选择测试模式:")
    print("1. 运行预定义测试规则")
    print("2. 自定义规则测试")
    print("3. 快速验证单个规则")

    choice = input("\n请选择 (1/2/3): ").strip()

    if choice == '1':
        print("\n运行预定义测试规则:")
        for i, rule_set in enumerate(test_rules, 1):
            print(f"\n{i}. {rule_set['name']}")
            test_rule(**rule_set)

    elif choice == '2':
        print("\n自定义规则测试:")
        buy_rule = input("加仓规则 (留空跳过): ").strip() or None
        sell_rule = input("平仓规则 (留空跳过): ").strip() or None
        open_rule = input("开仓规则 (留空跳过): ").strip() or None
        close_rule = input("清仓规则 (留空跳过): ").strip() or None

        if any([buy_rule, sell_rule, open_rule, close_rule]):
            test_rule(buy_rule, sell_rule, open_rule, close_rule)
        else:
            print("❌ 至少需要一个规则")

    elif choice == '3':
        print("\n快速验证单个规则:")
        rule = input("输入规则表达式: ").strip()
        if rule:
            test_rule(buy_rule=rule)
        else:
            print("❌ 规则不能为空")

    else:
        print("❌ 无效选择")

if __name__ == "__main__":
    main()