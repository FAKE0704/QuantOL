#!/usr/bin/env python3
"""
独立规则测试脚本
不依赖Streamlit，直接测试规则解析器功能
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

# 模拟st.session_state
class MockSessionState:
    def __init__(self):
        self.db = Mock()
        self.db._loop = Mock()
        self.db.load_stock_data = Mock()
        self.db.load_multiple_stock_data = Mock()
        self.db.get_all_stocks = Mock()

# 创建模拟的streamlit模块
class MockStreamlit:
    class session_state:
        db = Mock()
        db._loop = Mock()
        db.load_stock_data = Mock()
        db.load_multiple_stock_data = Mock()
        db.get_all_stocks = Mock()

# 将模拟的streamlit添加到sys.modules
sys.modules['streamlit'] = MockStreamlit()

from src.core.strategy.rule_parser import RuleParser
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

def test_rule_directly(buy_rule, sell_rule="", open_rule="", close_rule="", days=100):
    """直接测试规则解析器"""
    print(f"🧪 测试规则:")
    print(f"   开仓: {open_rule or '无'}")
    print(f"   清仓: {close_rule or '无'}")
    print(f"   加仓: {buy_rule or '无'}")
    print(f"   平仓: {sell_rule or '无'}")
    print("-" * 50)

    try:
        # 创建测试数据
        data = create_test_data(days)
        print(f"📊 生成测试数据: {len(data)} 天")

        # 创建指标服务和规则解析器
        indicator_service = IndicatorService()
        parser = RuleParser(data, indicator_service)

        # 测试所有规则
        rules = [
            ("开仓", open_rule),
            ("清仓", close_rule),
            ("加仓", buy_rule),
            ("平仓", sell_rule)
        ]

        signals = []
        for rule_name, rule_expr in rules:
            if rule_expr:
                print(f"\n🔍 测试{rule_name}规则: {rule_expr}")

                # 在不同位置测试规则
                rule_signals = []
                for i in range(20, len(data)):  # 跳过前面数据不足的位置
                    try:
                        result = parser.evaluate_at(rule_expr, i)
                        if result:
                            rule_signals.append({
                                'date': data.iloc[i]['combined_time'],
                                'price': data.iloc[i]['close'],
                                'index': i
                            })
                    except Exception as e:
                        print(f"   ❌ 位置 {i} 错误: {e}")
                        break

                if rule_signals:
                    print(f"   ✅ {rule_name}信号: {len(rule_signals)} 个")
                    for signal in rule_signals[:3]:  # 显示前3个信号
                        print(f"      {signal['date'].strftime('%Y-%m-%d')} @ {signal['price']:.2f}")
                    if len(rule_signals) > 3:
                        print(f"      ... 还有 {len(rule_signals) - 3} 个信号")
                else:
                    print(f"   ⚪ {rule_name}信号: 0 个")

                signals.extend(rule_signals)

        # 分析调试数据
        print(f"\n🐛 调试数据分析:")
        print(f"   数据总列数: {len(parser.data.columns)}")

        # 分类列
        basic_cols = ['open', 'high', 'low', 'close', 'volume', 'code', 'combined_time']
        indicator_cols = [col for col in parser.data.columns
                         if any(func in col for func in ['SMA', 'RSI', 'MACD', 'REF'])]
        rule_cols = [col for col in parser.data.columns
                    if col not in basic_cols and col not in indicator_cols]

        print(f"   基础数据列: {len(basic_cols)}")
        print(f"   指标列: {len(indicator_cols)}")
        if indicator_cols:
            print(f"     {', '.join(indicator_cols[:5])}{'...' if len(indicator_cols) > 5 else ''}")
        print(f"   规则结果列: {len(rule_cols)}")
        if rule_cols:
            print(f"     {', '.join(rule_cols[:5])}{'...' if len(rule_cols) > 5 else ''}")

        # 显示部分数据示例
        print(f"\n📄 数据示例 (最后5行):")
        display_cols = ['combined_time', 'close'] + indicator_cols[:3] + rule_cols[:2]
        available_cols = [col for col in display_cols if col in parser.data.columns]
        if available_cols:
            sample_data = parser.data[available_cols].tail().round(2)
            print(sample_data.to_string(index=False))

        print(f"\n✅ 测试完成")
        print(f"   总信号数: {len(signals)}")
        print(f"   数据列数: {len(parser.data.columns)}")

        return {
            'success': True,
            'signals': signals,
            'columns': len(parser.data.columns),
            'indicator_columns': indicator_cols,
            'rule_columns': rule_cols
        }

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return {
            'success': False,
            'error': str(e)
        }

def main():
    """主函数 - 交互式规则测试"""
    print("🎯 独立规则测试工具 (无Streamlit依赖)")
    print("=" * 60)

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
        },
        {
            'name': '复杂嵌套策略',
            'buy_rule': 'REF(SMA(close,5),1) < SMA(close,5) & REF(RSI(close,14),1) < RSI(close,14)',
            'sell_rule': 'SMA(close,5) < SMA(close,20) & RSI(close,14) > 60'
        }
    ]

    print("选择测试模式:")
    print("1. 运行预定义测试规则")
    print("2. 自定义规则测试")
    print("3. 快速验证单个规则")

    try:
        choice = input("\n请选择 (1/2/3): ").strip()

        if choice == '1':
            print("\n运行预定义测试规则:")
            for i, rule_set in enumerate(test_rules, 1):
                print(f"\n{'='*40}")
                print(f"{i}. {rule_set['name']}")
                print('='*40)
                test_rule_directly(**rule_set)

        elif choice == '2':
            print("\n自定义规则测试:")
            buy_rule = input("加仓规则 (留空跳过): ").strip() or None
            sell_rule = input("平仓规则 (留空跳过): ").strip() or None
            open_rule = input("开仓规则 (留空跳过): ").strip() or None
            close_rule = input("清仓规则 (留空跳过): ").strip() or None

            if any([buy_rule, sell_rule, open_rule, close_rule]):
                test_rule_directly(buy_rule, sell_rule, open_rule, close_rule)
            else:
                print("❌ 至少需要一个规则")

        elif choice == '3':
            print("\n快速验证单个规则:")
            rule = input("输入规则表达式: ").strip()
            if rule:
                test_rule_directly(buy_rule=rule)
            else:
                print("❌ 规则不能为空")

        else:
            print("❌ 无效选择")

    except KeyboardInterrupt:
        print("\n\n👋 测试已取消")
    except Exception as e:
        print(f"\n❌ 运行错误: {e}")

if __name__ == "__main__":
    main()