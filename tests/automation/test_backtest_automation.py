#!/usr/bin/env python3
"""
自动化回测测试套件
用于测试规则解析器和回测引擎的各种功能，无需手动界面操作
"""

import os
import sys
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any
import asyncio
from pathlib import Path
from unittest.mock import Mock, MagicMock

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

# 模拟Streamlit session_state
class MockSessionState:
    def __init__(self):
        self.db = Mock()
        # 模拟数据库管理器的方法
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
from src.core.data.market_data_source import MarketDataSource
from src.support.log.logger import logger

class BacktestAutomation:
    """自动化回测测试类"""

    def __init__(self):
        self.results = []
        self.test_data = self._create_test_data()
        self.indicator_service = IndicatorService()

    def _create_test_data(self) -> pd.DataFrame:
        """创建测试用市场数据"""
        np.random.seed(42)  # 确保可重复性

        # 生成100天的模拟数据
        dates = pd.date_range(start='2024-01-01', periods=100, freq='D')

        # 模拟价格走势（包含趋势和随机波动）
        base_price = 100
        prices = [base_price]
        for i in range(1, 100):
            change = np.random.normal(0.001, 0.02)  # 0.1%平均涨幅，2%波动率
            new_price = prices[-1] * (1 + change)
            prices.append(max(new_price, 1))  # 价格不能为负

        # 生成OHLCV数据
        data = []
        for i, (date, close) in enumerate(zip(dates, prices)):
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

    def create_test_config(self, strategy_type: str, rules: Dict[str, str]) -> BacktestConfig:
        """创建测试配置"""
        return BacktestConfig(
            start_date='20240101',
            end_date='20240410',
            target_symbol='test.000001',
            frequency='d',
            initial_capital=100000,
            commission_rate=0.0003,
            strategy_type=strategy_type,
            position_strategy_type="fixed_percent",
            position_strategy_params={"percent": 0.1},
            extra_params=rules
        )

    async def run_single_test(self, test_name: str, config: BacktestConfig) -> Dict[str, Any]:
        """运行单个测试用例"""
        print(f"🧪 运行测试: {test_name}")

        try:
            # 创建回测引擎
            engine = BacktestEngine(config=config, data=self.test_data)

            # 注册策略
            if config.strategy_type == "自定义规则":
                rules = config.extra_params or {}
                strategy = RuleBasedStrategy(
                    Data=self.test_data,
                    name=f"测试策略_{test_name}",
                    indicator_service=self.indicator_service,
                    buy_rule_expr=rules.get('buy_rule', ''),
                    sell_rule_expr=rules.get('sell_rule', ''),
                    open_rule_expr=rules.get('open_rule', ''),
                    close_rule_expr=rules.get('close_rule', ''),
                    portfolio_manager=engine.portfolio_manager
                )
                engine.register_strategy(strategy)

            # 运行回测
            start_date = pd.to_datetime(config.start_date)
            end_date = pd.to_datetime(config.end_date)
            engine.run(start_date, end_date)

            # 获取结果
            results = engine.get_results()

            # 验证调试数据
            debug_data_exists = "debug_data" in results and results["debug_data"]

            test_result = {
                'test_name': test_name,
                'status': 'PASSED',
                'config': config,
                'summary': results.get('summary', {}),
                'trades_count': len(results.get('trades', [])),
                'errors': results.get('errors', []),
                'debug_data_exists': debug_data_exists,
                'debug_data_columns': self._analyze_debug_data(results.get('debug_data', {})),
                'execution_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }

            print(f"✅ 测试通过: {test_name} - 交易次数: {test_result['trades_count']}")
            return test_result

        except Exception as e:
            error_msg = f"测试失败: {str(e)}"
            print(f"❌ {error_msg}")
            return {
                'test_name': test_name,
                'status': 'FAILED',
                'error': error_msg,
                'config': config,
                'execution_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }

    def _analyze_debug_data(self, debug_data: Dict) -> Dict[str, Any]:
        """分析调试数据结构"""
        if not debug_data:
            return {}

        analysis = {}
        for strategy_name, data in debug_data.items():
            if data is not None and hasattr(data, 'columns'):
                cols = list(data.columns)
                analysis[strategy_name] = {
                    'total_columns': len(cols),
                    'basic_columns': [c for c in cols if c in ['open', 'high', 'low', 'close', 'volume', 'code', 'combined_time']],
                    'indicator_columns': [c for c in cols if any(func in c for func in ['SMA', 'RSI', 'MACD', 'REF'])],
                    'rule_columns': [c for c in cols if c not in ['open', 'high', 'low', 'close', 'volume', 'code', 'combined_time'] and not any(func in c for func in ['SMA', 'RSI', 'MACD', 'REF'])]
                }

        return analysis

    async def run_test_suite(self) -> List[Dict[str, Any]]:
        """运行完整的测试套件"""
        print("🚀 开始自动化回测测试套件")
        print("=" * 60)

        # 定义测试用例
        test_cases = [
            {
                'name': '基础SMA策略',
                'config': self.create_test_config("自定义规则", {
                    'buy_rule': 'SMA(close,5) > SMA(close,20)',
                    'sell_rule': 'SMA(close,5) < SMA(close,20)'
                })
            },
            {
                'name': 'RSI超买超卖策略',
                'config': self.create_test_config("自定义规则", {
                    'buy_rule': 'RSI(close,14) < 30',
                    'sell_rule': 'RSI(close,14) > 70'
                })
            },
            {
                'name': '多重条件策略',
                'config': self.create_test_config("自定义规则", {
                    'buy_rule': 'SMA(close,5) > SMA(close,20) & RSI(close,14) < 50',
                    'sell_rule': 'SMA(close,5) < SMA(close,20) | RSI(close,14) > 70'
                })
            },
            {
                'name': 'REF函数策略',
                'config': self.create_test_config("自定义规则", {
                    'buy_rule': 'REF(SMA(close,5),1) < SMA(close,5)',
                    'sell_rule': 'REF(SMA(close,5),1) > SMA(close,5)'
                })
            },
            {
                'name': '复杂嵌套策略',
                'config': self.create_test_config("自定义规则", {
                    'buy_rule': 'REF(SMA(close,5),1) < SMA(close,5) & REF(RSI(close,14),1) < RSI(close,14)',
                    'sell_rule': 'SMA(close,5) < SMA(close,20) & RSI(close,14) > 60'
                })
            }
        ]

        # 运行所有测试
        for test_case in test_cases:
            result = await self.run_single_test(
                test_case['name'],
                test_case['config']
            )
            self.results.append(result)

        # 生成测试报告
        self._generate_report()

        return self.results

    def _generate_report(self):
        """生成测试报告"""
        print("\n" + "=" * 60)
        print("📊 测试报告")
        print("=" * 60)

        passed = len([r for r in self.results if r['status'] == 'PASSED'])
        failed = len([r for r in self.results if r['status'] == 'FAILED'])

        print(f"总测试数: {len(self.results)}")
        print(f"通过: {passed}")
        print(f"失败: {failed}")
        print(f"成功率: {passed/len(self.results)*100:.1f}%")

        print("\n详细结果:")
        for result in self.results:
            status_icon = "✅" if result['status'] == 'PASSED' else "❌"
            print(f"{status_icon} {result['test_name']}")

            if result['status'] == 'PASSED':
                print(f"   - 交易次数: {result['trades_count']}")
                print(f"   - 调试数据: {'✅' if result['debug_data_exists'] else '❌'}")

                if result['debug_data_columns']:
                    for strategy, cols in result['debug_data_columns'].items():
                        print(f"   - {strategy}: {cols['total_columns']}列 (指标:{len(cols['indicator_columns'])}, 规则:{len(cols['rule_columns'])})")
            else:
                print(f"   - 错误: {result.get('error', 'Unknown error')}")

        # 保存报告到文件
        self._save_report_to_file()

    def _save_report_to_file(self):
        """保存报告到JSON文件"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = project_root / f"test_report_{timestamp}.json"

        report_data = {
            'timestamp': timestamp,
            'summary': {
                'total_tests': len(self.results),
                'passed': len([r for r in self.results if r['status'] == 'PASSED']),
                'failed': len([r for r in self.results if r['status'] == 'FAILED'])
            },
            'results': self.results
        }

        # 转换不可序列化的对象
        def make_serializable(obj):
            if isinstance(obj, BacktestConfig):
                return {
                    'strategy_type': obj.strategy_type,
                    'start_date': obj.start_date,
                    'end_date': obj.end_date,
                    'target_symbol': obj.target_symbol,
                    'extra_params': obj.extra_params
                }
            elif hasattr(obj, '__dict__'):
                return str(obj)
            return obj

        serializable_results = []
        for result in self.results:
            serializable_result = {}
            for key, value in result.items():
                serializable_result[key] = make_serializable(value)
            serializable_results.append(serializable_result)

        report_data['results'] = serializable_results

        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)

        print(f"\n📄 详细报告已保存到: {report_file}")

async def main():
    """主函数"""
    automation = BacktestAutomation()
    await automation.run_test_suite()

if __name__ == "__main__":
    asyncio.run(main())