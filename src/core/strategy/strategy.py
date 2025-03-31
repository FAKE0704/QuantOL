import logging
import streamlit as st
import pandas as pd
from datetime import datetime
from typing import Dict, Any
from core.strategy.events import ScheduleEvent
from core.strategy.backtesting import BacktestEngine

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

    def handle_event(self, engine, event):
        """统一事件处理入口"""
        if isinstance(event, ScheduleEvent):
            if event.schedule_type == "MONTHLY":
                self.on_monthly_schedule(engine, event)
                
    def on_monthly_schedule(self, engine, event):
        """每月定时回调（子类可覆盖）"""
        pass

class FixedInvestmentStrategy(BaseStrategy):
    def __init__(self, Data, name, buySignal, sellSignal):
        super().__init__(Data, name, buySignal, sellSignal)
        self.invest_ratio = 0.01  # 定投比例

    def on_monthly_schedule(self, engine:BacktestEngine, event:ScheduleEvent):
        """每月定投逻辑"""
        # 计算定投金额
        invest_amount = engine.config.initial_capital * self.invest_ratio
        # 获取当前价格并转换为float
        current_price = float(engine.data.iloc[-1]["close"])
        # 计算可买数量并取整
        quantity = int(invest_amount / current_price)
        
        # 直接创建订单
        engine.create_order(
            symbol=engine.config.target_symbol,
            quantity=quantity,
            side="BUY",
            price=current_price
        )

    def get_required_events(self):
        return [ScheduleEvent]










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
