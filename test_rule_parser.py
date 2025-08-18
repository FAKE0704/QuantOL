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
    data = {'close': [i for i in range(1, 21)]}  # 20个数据点[1,2,...,20]
    print(data)
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

if __name__ == '__main__':
    test_ref_sma()
