import pandas as pd
from src.core.strategy.rule_parser import RuleParser
from src.core.strategy.indicators import IndicatorService

class MockIndicatorService(IndicatorService):
    def calculate_indicator(self, func_name, series, current_index, *args):
        if func_name.upper() == 'SMA':
            period = args[0] if args else 5
            print(f"SMA计算: 当前索引={current_index}, 周期={period}")
            if current_index < period - 1:  # 不足period长度
                print("数据不足，返回0")
                return 0.0
            window = series.iloc[current_index-period+1:current_index+1]
            print(f"窗口数据: {window.values}")
            if len(window) != period:  # 边界检查
                print("窗口长度不符，返回0")
                return 0.0
            result = window.mean()
            print(f"SMA计算结果: {result}")
            return result
        return 0.0

def test_ref_sma():
    # 准备测试数据
    data = {'close': [6.4, 6.62, 6.64, 5.98, 5.56, 5.67, 5.97, 6.06, 6.22, 6.23, 6.17, 6.79, 6.34, 6.97, 6.82, 6.18, 5.92, 5.94, 6.09, 6.1, 6.71]}  # 数据点
    # sma(3)  [na,na,3,4.5,...]
    df = pd.DataFrame(data)
    
    # 初始化解析器
    indicator_service = MockIndicatorService()
    parser = RuleParser(df, indicator_service)
    
    # 测试表达式
    test_expr = 'REF(SMA(close,3),1)'
    print(f'测试表达式: {test_expr}')
    
    # 在不同位置测试
    for i in [1, 2, 3, 4, 5, 6]:  # 测试不同位置
        parser.current_index = i
        result = parser.parse(test_expr, mode='ref')
        print(f'位置 {i}: {result}')

def test_signal():
    # 准备测试数据 (保持原有数据不变)
    data = {'close': [6.4, 6.62, 6.64, 5.98, 5.56, 5.67, 5.97, 6.06, 6.22, 6.23, 6.17, 6.79, 6.34, 6.97, 6.82, 6.18, 5.92, 5.94, 6.09, 6.1, 6.71]}
    df = pd.DataFrame(data)
    
    # 初始化解析器
    indicator_service = MockIndicatorService()
    parser = RuleParser(df, indicator_service)
    
    # 测试SMA(close,3)计算和存储
    parser.current_index = 6
    sma_value = parser.parse("SMA(close,3)", mode='ref')
    
    # 验证计算结果和存储
    expected_sma = (5.67 + 5.97 + 6.06)/3
    print( abs(sma_value - expected_sma) < 0.001)
    print( "SMA(close,3)" in parser.data.columns)
    print( abs(parser.data.at[6, "SMA(close,3)"] - expected_sma) < 0.001)
    
    # 测试REF函数
    parser.current_index = 8
    ref_value = parser.parse("REF(SMA(close,3),2)", mode='ref')
    print( abs(ref_value - expected_sma) < 0.001 ) # 应返回第6位置的SMA值

if __name__ == '__main__':
    test_ref_sma()
    test_signal()  # 新增测试调用
