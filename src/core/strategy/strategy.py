import streamlit as st
import pandas as pd
import logging
from datetime import datetime
from typing import Dict, Any, Type, Callable
from event_bus.event_types import StrategyScheduleEvent, BaseEvent
from core.strategy.backtesting import BacktestEngine

class BaseStrategy():
    def __init__(self, Data, name, buy_rule_expr="", sell_rule_expr="", invest_ratio=0.01):
        import uuid
        self.logger = logging.getLogger(__name__)  # 使用标准logging
        self.Data = Data
        self.name : str = name
        self.buy_rule_expr = buy_rule_expr
        self.sell_rule_expr = sell_rule_expr
        self.strategy_id = str(uuid.uuid4())  # 生成唯一ID
        self.position_cost = 0.0  # 平均持仓成本
        self.position_size = 0.0  # 当前持仓数量
        self.position_records = []  # 分笔持仓记录

    def update_position(self, quantity: float, price: float):
        """更新持仓成本和数量"""
        if quantity > 0:  # 买入
            new_cost = self.position_cost * self.position_size + quantity * price
            self.position_size += quantity
            self.position_cost = new_cost / self.position_size
            self.position_records.append({
                'quantity': quantity,
                'price': price,
                'timestamp': datetime.now()
            })
        else:  # 卖出
            sold_qty = abs(quantity)
            remaining_qty = self.position_size - sold_qty
            if remaining_qty < 0:
                raise ValueError("卖出数量超过持仓量")
                
            # 先进先出原则计算成本
            total_cost = 0
            while sold_qty > 0 and self.position_records:
                oldest = self.position_records[0]
                if oldest['quantity'] <= sold_qty:
                    total_cost += oldest['quantity'] * oldest['price']
                    sold_qty -= oldest['quantity']
                    self.position_records.pop(0)
                else:
                    total_cost += sold_qty * oldest['price']
                    oldest['quantity'] -= sold_qty
                    sold_qty = 0
            self.position_cost = total_cost / abs(quantity) if quantity !=0 else 0
            self.position_size = remaining_qty
            
        self.logger.debug(f"策略仓位更新 | 数量: {self.position_size} | 成本: {self.position_cost}") #debug
        # 返回更新后的仓位信息
        return {
            'position_size': self.position_size,
            'position_cost': self.position_cost,
            'timestamp': datetime.now()
        }

    def get_strategy(self):
        return f"strategy name: {self.name}"

    def handle_event(self, engine, event):
        """统一事件处理入口"""
        if isinstance(event, StrategyScheduleEvent):
            if event.schedule_type == "MONTHLY":
                self.on_monthly_schedule(engine, event)
                
    def on_monthly_schedule(self, engine, event):
        """每月定时回调（子类可覆盖）"""
        pass

class FixedInvestmentStrategy(BaseStrategy):
    def __init__(self, Data, name, buy_rule_expr="", sell_rule_expr=""):
        super().__init__(Data, name, buy_rule_expr, sell_rule_expr)
        self.invest_ratio = 0.01  # 定投比例
        

    def on_monthly_schedule(self, engine:BacktestEngine, event:StrategyScheduleEvent):
        """每月定投逻辑"""
        # 计算定投金额
        invest_amount = engine.config.initial_capital * self.invest_ratio
        # 获取当前价格并转换为float
        current_price = float(engine.data.iloc[-1]["close"])
        # 计算可买数量并取整
        quantity = int(invest_amount / current_price)
        
        # 直接创建订单
        engine.create_order(
            event.timestamp,
            symbol=engine.config.target_symbol,
            quantity=quantity,
            side="BUY",
            price=current_price,
            strategy_id=self.strategy_id
        )
    def set_name(self,name :str):
        self.name = name
        return name

    def get_required_events(self):
        return [StrategyScheduleEvent]










# 主程序
if __name__ == "__main__":
    pass
