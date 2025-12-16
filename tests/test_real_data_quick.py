#!/usr/bin/env python3
"""
快速测试脚本 - 专门针对tests/data/2025-10-30T19-02_export.csv
直接使用真实的市场数据进行规则验证
"""

import os
import sys
import pandas as pd
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

def load_stock600604_data():
    """加载sh.600604的真实数据"""
    csv_path = "tests/data/2025-10-30T19-02_export.csv"

    if not os.path.exists(csv_path):
        print(f"❌ 数据文件不存在: {csv_path}")
        return None

    print(f"📁 加载数据文件: {csv_path}")

    try:
        # 读取CSV文件
        df = pd.read_csv(csv_path)

        print(f"📊 原始数据信息:")
        print(f"   记录数: {len(df)}")
        print(f"   列数: {len(df.columns)}")
        print(f"   列名: {list(df.columns)}")

        # 数据预处理
        # 检查数据格式
        if 'combined_time' in df.columns:
            df['combined_time'] = pd.to_datetime(df['combined_time'])
        elif 'date' in df.columns and 'time' in df.columns:
            df['combined_time'] = pd.to_datetime(df['date'] + ' ' + df['time'])
        else:
            print("❌ 未找到时间列")
            return None

        # 确保数值列类型正确
        numeric_cols = ['open', 'high', 'low', 'close', 'volume']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

        # 处理空值
        null_counts = df[numeric_cols].isnull().sum()
        if null_counts.any():
            print(f"⚠️ 发现空值: {null_counts[null_counts > 0].to_dict()}")
            # 前向填充和后向填充
            df[numeric_cols] = df[numeric_cols].fillna(method='ffill').fillna(method='bfill')

        # 过滤掉价格为0或负数的记录
        df = df[df['close'] > 0]

        # 按时间排序
        df = df.sort_values('combined_time').reset_index(drop=True)

        # 显示数据统计
        print(f"\n📈 数据统计:")
        print(f"   有效记录数: {len(df)}")
        print(f"   时间范围: {df['combined_time'].min()} 至 {df['combined_time'].max()}")
        print(f"   价格范围: {df['close'].min():.2f} - {df['close'].max():.2f}")
        print(f"   平均价格: {df['close'].mean():.2f}")
        print(f"   总成交量: {df['volume'].sum():,}")

        # 显示前几行数据
        print(f"\n📋 数据示例 (前3行):")
        sample_cols = ['combined_time', 'open', 'high', 'low', 'close', 'volume']
        available_cols = [col for col in sample_cols if col in df.columns]
        print(df[available_cols].head(3).to_string(index=False))

        return df

    except Exception as e:
        print(f"❌ 数据加载失败: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_strategy_on_real_data(data, strategy_name, rules):
    """在真实数据上测试策略"""
    print(f"\n{'='*60}")
    print(f"🧪 测试策略: {strategy_name}")
    print('='*60)

    try:
        # 创建指标服务和规则解析器
        indicator_service = IndicatorService()
        parser = RuleParser(data, indicator_service)

        print(f"📋 规则配置:")
        for rule_type, rule_expr in rules.items():
            if rule_expr:
                print(f"   {rule_type}: {rule_expr}")

        total_signals = 0
        signal_details = {}

        # 测试每个规则
        for rule_type, rule_expr in rules.items():
            if not rule_expr:
                continue

            print(f"\n🔍 测试 {rule_type} 规则...")

            signals = []
            start_idx = 20  # 从第20条开始，确保有足够历史数据

            for i in range(start_idx, len(data)):
                try:
                    result = parser.evaluate_at(rule_expr, i)
                    if result:
                        signals.append({
                            'date': data.iloc[i]['combined_time'],
                            'price': data.iloc[i]['close'],
                            'index': i,
                            'volume': data.iloc[i]['volume'] if 'volume' in data.columns else None
                        })
                except Exception as e:
                    print(f"   ❌ 位置 {i} 错误: {e}")
                    break

            signal_details[rule_type] = signals
            total_signals += len(signals)

            if signals:
                print(f"   ✅ {rule_type} 信号: {len(signals)} 个")

                # 显示前3个和后3个信号
                display_count = min(6, len(signals))
                if len(signals) <= 3:
                    display_signals = signals
                else:
                    display_signals = signals[:3] + signals[-3:]

                for signal in display_signals:
                    date_str = signal['date'].strftime('%Y-%m-%d')
                    price_str = f"{signal['price']:.2f}"
                    vol_str = f" vol:{signal['volume']:,}" if signal['volume'] else ""
                    print(f"      {date_str} @ {price_str} {vol_str}")

                if len(signals) > 6:
                    print(f"      ... 还有 {len(signals) - 6} 个信号")
            else:
                print(f"   ⚪ {rule_type} 信号: 0 个")

        # 调试数据分析
        print(f"\n🐛 调试数据分析:")
        print(f"   数据总列数: {len(parser.data.columns)}")

        basic_cols = ['open', 'high', 'low', 'close', 'volume', 'code', 'combined_time']
        indicator_cols = [col for col in parser.data.columns
                         if any(func in col for func in ['SMA', 'RSI', 'MACD', 'REF'])]
        rule_cols = [col for col in parser.data.columns
                    if col not in basic_cols and col not in indicator_cols]

        print(f"   基础数据列: {len(basic_cols)}")
        print(f"   指标列: {len(indicator_cols)}")
        if indicator_cols:
            print(f"     {', '.join(indicator_cols)}")
        print(f"   规则结果列: {len(rule_cols)}")
        if rule_cols:
            print(f"     {', '.join(rule_cols)}")

        # 显示数据示例
        print(f"\n📄 处理后数据示例 (最后3行):")
        display_cols = ['combined_time', 'close'] + indicator_cols[:2] + rule_cols[:1]
        available_cols = [col for col in display_cols if col in parser.data.columns]
        if available_cols:
            sample_data = parser.data[available_cols].tail(3).round(2)
            print(sample_data.to_string(index=False))

        print(f"\n📊 策略总结:")
        print(f"   总信号数: {total_signals}")
        print(f"   数据覆盖: {len(data)} 个交易日")
        print(f"   信号频率: {total_signals/len(data)*100:.2f}%")

        return {
            'success': True,
            'strategy_name': strategy_name,
            'total_signals': total_signals,
            'signal_details': signal_details,
            'data_rows': len(data)
        }

    except Exception as e:
        print(f"❌ 策略测试失败: {e}")
        import traceback
        traceback.print_exc()
        return {
            'success': False,
            'strategy_name': strategy_name,
            'error': str(e)
        }

def main():
    """主函数"""
    print("🎯 sh.600604 真实数据策略测试")
    print("=" * 60)

    # 加载数据
    data = load_stock600604_data()
    if data is None:
        print("❌ 无法加载数据，退出测试")
        return

    # 定义测试策略
    strategies = [
        {
            'name': 'SMA金叉死叉策略',
            'rules': {
                'buy_rule': 'SMA(close,5) > SMA(close,20) & REF(SMA(close,5),1) <= REF(SMA(close,20),1)',
                'sell_rule': 'SMA(close,5) < SMA(close,20) & REF(SMA(close,5),1) >= REF(SMA(close,20),1)'
            }
        },
        {
            'name': 'RSI超买超卖策略',
            'rules': {
                'buy_rule': 'RSI(close,14) < 30 & REF(RSI(close,14),1) >= 30',
                'sell_rule': 'RSI(close,14) > 70 & REF(RSI(close,14),1) <= 70'
            }
        },
        {
            'name': '价格突破策略',
            'rules': {
                'buy_rule': 'close > REF(high,10) & close > SMA(close,20)',
                'sell_rule': 'close < REF(low,10) & close < SMA(close,20)'
            }
        },
        {
            'name': 'MACD策略',
            'rules': {
                'buy_rule': 'MACD(close,12,26,9) > MACD_SIGNAL(close,12,26,9) & REF(MACD(close,12,26,9),1) <= REF(MACD_SIGNAL(close,12,26,9),1)',
                'sell_rule': 'MACD(close,12,26,9) < MACD_SIGNAL(close,12,26,9) & REF(MACD(close,12,26,9),1) >= REF(MACD_SIGNAL(close,12,26,9),1)'
            }
        },
        {
            'name': '组合策略',
            'rules': {
                'buy_rule': '(SMA(close,5) > SMA(close,20)) & (RSI(close,14) < 50)',
                'sell_rule': '(SMA(close,5) < SMA(close,20)) | (RSI(close,14) > 80)'
            }
        }
    ]

    # 运行所有策略测试
    results = []
    for strategy in strategies:
        result = test_strategy_on_real_data(data, strategy['name'], strategy['rules'])
        results.append(result)

    # 生成汇总报告
    print(f"\n{'='*60}")
    print("📊 策略测试汇总报告")
    print('='*60)

    successful_results = [r for r in results if r['success']]
    failed_results = [r for r in results if not r['success']]

    print(f"✅ 成功测试: {len(successful_results)} 个策略")
    print(f"❌ 失败测试: {len(failed_results)} 个策略")

    if successful_results:
        print(f"\n📈 成功策略详情:")
        for result in successful_results:
            print(f"   {result['strategy_name']}: {result['total_signals']} 个信号 "
                  f"({result['total_signals']/result['data_rows']*100:.2f}% 信号频率)")

    if failed_results:
        print(f"\n❌ 失败策略详情:")
        for result in failed_results:
            print(f"   {result['strategy_name']}: {result['error']}")

    print(f"\n🎯 推荐策略:")
    if successful_results:
        # 找到信号数量适中的策略（不要太多也不要太少）
        reasonable_results = [r for r in successful_results
                            if 5 <= r['total_signals'] <= 50]
        if reasonable_results:
            best = min(reasonable_results, key=lambda x: abs(x['total_signals'] - 20))
            print(f"   {best['strategy_name']} - 信号数量适中 ({best['total_signals']} 个)")
        else:
            best = max(successful_results, key=lambda x: x['total_signals'])
            print(f"   {best['strategy_name']} - 最多信号 ({best['total_signals']} 个)")

    print(f"\n✅ 测试完成!")

if __name__ == "__main__":
    main()