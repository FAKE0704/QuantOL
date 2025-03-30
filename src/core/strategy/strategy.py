import logging
import streamlit as st
import pandas as pd
from datetime import datetime
from typing import Dict, Any

class BaseEvent:
    """事件基类"""
    def __init__(self, timestamp: datetime, event_type: str):
        self.timestamp = timestamp
        self.event_type = event_type

    def to_dict(self) -> Dict[str, Any]:
        """将事件转换为字典"""
        return {
            'timestamp': self.timestamp.isoformat(),
            'event_type': self.event_type
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BaseEvent':
        """从字典创建事件"""
        return cls(
            timestamp=datetime.fromisoformat(data['timestamp']),
            event_type=data['event_type']
        )

    def __lt__(self, other: 'BaseEvent') -> bool:
        """用于事件队列的优先级比较"""
        return self.timestamp < other.timestamp




from queue import PriorityQueue
from typing import Type, Callable, Dict



class BaseStrategy():
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
