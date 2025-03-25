import logging
import streamlit as st
import pandas as pd

# 写点方法

class Strategy():
    def __init__(self,Data,name,buySignal,sellSignal):
        self.Data = Data
        self.name : str = name
        self.buySignal  = buySignal
        self.sellSignal  = sellSignal

    def get_strategy(self):
        return f"strategy name: {self.name}"










# 主程序
if __name__ == "__main__":
    # 初始化数据提供者和策略
    data_provider = MockDataProvider()
    strategy = SimpleMovingAverageStrategy()

    # 初始化交易系统
    trading_system = TradingSystem(data_provider, strategy)

    # 更新数据
    trading_system.data_update()

    # 加载策略并计算指标
    trading_system.load_strategy()

    # 模拟交易
    trading_system.buy(amount=1000)
    trading_system.sell(amount=1000)

