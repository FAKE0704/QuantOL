import pandas as pd
import unittest
from rule_parser import RuleParser
from .indicators import IndicatorService

class TestRuleParser(unittest.TestCase):
    def setUp(self):
        # 创建测试数据
        # 扩展测试数据以支持20周期SMA计算
        data = {
            'open': [10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30],
            'high': [11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31],
            'low': [9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29],
            'close': [10.5,11.5,12.5,13.5,14.5,15.5,16.5,17.5,18.5,19.5,20.5,21.5,22.5,23.5,24.5,25.5,26.5,27.5,28.5,29.5,30.5],
            'volume': [100,200,300,400,500,600,700,800,900,1000,1100,1200,1300,1400,1500,1600,1700,1800,1900,2000,2100]
        }
        self.df = pd.DataFrame(data)
        self.indicator_service = IndicatorService()
        self.parser = RuleParser(self.df, self.indicator_service)

    def test_basic_sma(self):
        # 测试基本SMA调用
        result = self.parser.parse("SMA(5) > 10")
        self.assertTrue(result)
        
        result = self.parser.parse("SMA(close,5) > 10")
        self.assertTrue(result)

    def test_nested_function(self):
        # 测试嵌套函数调用
        result = self.parser.parse("REF(SMA(close,5),1) > 10")
        self.assertTrue(result)

    def test_invalid_params(self):
        # 测试无效参数
        with self.assertRaises(ValueError):
            self.parser.parse("SMA(0) > 10")
            
        with self.assertRaises(ValueError):
            self.parser.parse("SMA(abc,5) > 10")

    def test_complex_rule(self):
        # 测试复杂规则
        rule = "(SMA(5) > SMA(10)) & (RSI(14) < 30)"
        result = self.parser.parse(rule)
        self.assertIsInstance(result, bool)

    def test_buy_condition(self):
        # 测试买入条件
        rule = "REF(SMA(close,5),1) < REF(SMA(close,20),1) & SMA(close,5) > SMA(close,20)"
        result = self.parser.parse(rule)
        self.assertIsInstance(result, bool)

if __name__ == '__main__':
    unittest.main()
