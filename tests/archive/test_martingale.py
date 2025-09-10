#!/usr/bin/env python3
"""测试Martingale规则解析"""

import pandas as pd
import numpy as np
import sys
import os

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# 现在导入模块
try:
    from core.strategy.rule_parser import RuleParser
    from core.strategy.indicators import IndicatorService
    print("成功导入模块")
except ImportError as e:
    print(f"导入错误: {e}")
    print("创建模拟的IndicatorService和RuleParser")
    
    class IndicatorService:
        def calculate_indicator(self, func_name, series, index, *args):
            if func_name.lower() == 'sma':
                period = args[0] if args else 5
                start_idx = max(0, index - period + 1)
                return series.iloc[start_idx:index+1].mean()
            return 0.0
    
    # 创建模拟的RuleParser
    import ast
    import operator as op
    import pandas as pd
    
    class RuleParser:
        def __init__(self, data_provider, indicator_service, portfolio_manager=None):
            self.data = data_provider
            self.indicator_service = indicator_service
            self.portfolio_manager = portfolio_manager
            self.current_index = 0
        
        def evaluate_at(self, rule, index):
            self.current_index = index
            # 简单模拟评估
            return index % 2 == 0  # 简单返回True/False

# 创建测试数据
data = pd.DataFrame({
    'close': [100, 105, 98, 102, 95, 90, 85, 80, 75, 70],
    'code': ['TEST'] * 10
})

# 创建模拟的投资组合管理器
class MockPortfolioManager:
    def get_total_cost(self):
        return 5000  # 模拟总成本
    
    def get_position(self, symbol):
        class MockPosition:
            def __init__(self, quantity):
                self.quantity = quantity
        return MockPosition(100)  # 模拟持仓100股

# 创建指标服务
indicator_service = IndicatorService()
portfolio_manager = MockPortfolioManager()

# 创建规则解析器
parser = RuleParser(data, indicator_service, portfolio_manager)

# 测试Martingale规则表达式
martingale_rule = "(close - (COST / POSITION)) / (COST / POSITION) * 100 <= -5"

print("原始数据:")
print(data)
print("\n测试Martingale规则:", martingale_rule)

# 在多个位置测试规则
for i in range(len(data)):
    result = parser.evaluate_at(martingale_rule, i)
    print(f"索引 {i}: 规则结果 = {result}")

print("\n最终数据列:")
print("COST列:", "COST" in data.columns)
print("POSITION列:", "POSITION" in data.columns)
print("所有列:", list(data.columns))

# 检查是否生成了正确的布尔表达式列
bool_columns = [col for col in data.columns if data[col].dtype == bool]
print("布尔列:", bool_columns)

# 检查是否有数字常量被错误地存储为列
constant_columns = [col for col in data.columns if col.strip().lstrip('-').isdigit()]
print("数字常量列:", constant_columns)

# 检查中间表达式是否被错误存储
intermediate_exprs = [col for col in data.columns if 
                     col != "(close - (COST / POSITION)) / (COST / POSITION) * 100 <= -5" and
                     col != "COST" and col != "POSITION" and
                     not col.strip().lstrip('-').isdigit()]
print("中间表达式列:", intermediate_exprs)

# 验证修复结果
if "(close - (COST / POSITION)) / (COST / POSITION) * 100 <= -5" in data.columns:
    print("✓ 正确生成了布尔表达式列")
else:
    print("✗ 布尔表达式列未生成")

if "COST" in data.columns and "POSITION" in data.columns:
    print("✓ 正确生成了COST和POSITION列")
else:
    print("✗ COST/POSITION列未正确生成")

if not constant_columns:
    print("✓ 没有数字常量被错误存储为列")
else:
    print("✗ 数字常量被错误存储:", constant_columns)

if not intermediate_exprs:
    print("✓ 没有中间表达式被错误存储")
else:
    print("✗ 中间表达式被错误存储:", intermediate_exprs)