#!/usr/bin/env python3
"""
使用真实数据的规则测试脚本
支持加载CSV格式的真实市场数据进行规则测试
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

def load_real_data(csv_path: str) -> pd.DataFrame:
    """加载真实的市场数据CSV文件"""
    try:
        # 读取CSV文件
        df = pd.read_csv(csv_path)

        # 数据预处理
        # 确保列名标准化
        if 'date' in df.columns and 'time' in df.columns:
            # 合并日期和时间
            df['combined_time'] = pd.to_datetime(df['date'] + ' ' + df['time'])
        elif 'combined_time' in df.columns:
            df['combined_time'] = pd.to_datetime(df['combined_time'])
        else:
            raise ValueError("CSV文件中缺少时间列")

        # 确保数值列的数据类型正确
        numeric_columns = ['open', 'high', 'low', 'close', 'volume']
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

        # 填充或删除空值
        df = df.dropna(subset=['close'])  # 删除收盘价为空的行
        df = df.fillna(method='ffill').fillna(method='bfill')  # 前向填充和后向填充

        # 确保数据按时间排序
        df = df.sort_values('combined_time').reset_index(drop=True)

        print(f"✅ 成功加载真实数据: {len(df)} 条记录")
        print(f"   时间范围: {df['combined_time'].min()} 至 {df['combined_time'].max()}")
        print(f"   价格范围: {df['close'].min():.2f} - {df['close'].max():.2f}")

        return df

    except Exception as e:
        print(f"❌ 加载数据失败: {e}")
        return None

def create_sample_data(days=100) -> pd.DataFrame:
    """创建模拟数据（作为备用）"""
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

def test_rule_with_data(data: pd.DataFrame, buy_rule, sell_rule="", open_rule="", close_rule=""):
    """使用给定数据测试规则"""
    print(f"🧪 测试规则:")
    print(f"   开仓: {open_rule or '无'}")
    print(f"   清仓: {close_rule or '无'}")
    print(f"   加仓: {buy_rule or '无'}")
    print(f"   平仓: {sell_rule or '无'}")
    print("-" * 50)

    try:
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

                # 在不同位置测试规则（跳过前面数据不足的位置）
                rule_signals = []
                start_idx = 20  # 从第20条数据开始，确保有足够的历史数据
                for i in range(start_idx, len(data)):
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
                    # 显示前3个和后3个信号
                    display_signals = rule_signals[:3] + (rule_signals[-3:] if len(rule_signals) > 6 else [])
                    for signal in display_signals:
                        print(f"      {signal['date'].strftime('%Y-%m-%d')} @ {signal['price']:.2f}")
                    if len(rule_signals) > 6:
                        print(f"      ... 还有 {len(rule_signals) - 6} 个信号")
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
    print("🎯 真实数据规则测试工具")
    print("=" * 60)

    # 检查真实数据文件
    real_data_path = "tests/data/2025-10-30T19-02_export.csv"

    if os.path.exists(real_data_path):
        print(f"📁 发现真实数据文件: {real_data_path}")
        use_real = input("是否使用真实数据? (y/n, 默认y): ").strip().lower()

        if use_real in ['', 'y', 'yes']:
            print("🔄 加载真实数据...")
            data = load_real_data(real_data_path)
            if data is None:
                print("⚠️ 真实数据加载失败，使用模拟数据")
                data = create_sample_data()
        else:
            print("🔄 使用模拟数据")
            data = create_sample_data()
    else:
        print(f"⚠️ 未找到真实数据文件: {real_data_path}")
        print("🔄 使用模拟数据")
        data = create_sample_data()

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
        },
        {
            'name': '价格突破策略',
            'buy_rule': 'close > REF(high,5) & close > SMA(close,20)',
            'sell_rule': 'close < REF(low,5) & close < SMA(close,20)'
        }
    ]

    print("\n选择测试模式:")
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
                test_rule_with_data(data, **rule_set)

        elif choice == '2':
            print("\n自定义规则测试:")
            buy_rule = input("加仓规则 (留空跳过): ").strip() or None
            sell_rule = input("平仓规则 (留空跳过): ").strip() or None
            open_rule = input("开仓规则 (留空跳过): ").strip() or None
            close_rule = input("清仓规则 (留空跳过): ").strip() or None

            if any([buy_rule, sell_rule, open_rule, close_rule]):
                test_rule_with_data(data, buy_rule, sell_rule, open_rule, close_rule)
            else:
                print("❌ 至少需要一个规则")

        elif choice == '3':
            print("\n快速验证单个规则:")
            rule = input("输入规则表达式: ").strip()
            if rule:
                test_rule_with_data(data, buy_rule=rule)
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