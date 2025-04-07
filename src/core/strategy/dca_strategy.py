from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import List
from collections import deque
from ..events import MarketEvent, ScheduleEvent
from .strategy import BaseStrategy

class DCABaseStrategy(BaseStrategy):
    """定投策略基类"""
    
    def __init__(self, config, strategy_id: str = "dca_strategy"):
        super().__init__(config)
        self.strategy_id = strategy_id
        self.investment_dates = deque()
        self.scheduled_investment = config.monthly_investment
        self.generate_schedule()
        
    def generate_schedule(self):
        """生成定投计划"""
        start_date = datetime.strptime(self.config.start_date, "%Y-%m-%d")
        end_date = datetime.strptime(self.config.end_date, "%Y-%m-%d")
        
        current_date = start_date
        while current_date <= end_date:
            self.investment_dates.append(current_date)
            # 计算下个月同一天
            try:
                current_date = current_date.replace(month=current_date.month+1)
            except ValueError:
                # 处理月份超过12的情况
                current_date = current_date.replace(year=current_date.year+1, month=1)
        
    def adjust_for_holidays(self, date: datetime) -> datetime:
        """调整非交易日"""
        # 如果当天是周末，调整到下一个工作日
        while date.weekday() >= 5:  # 5=Saturday, 6=Sunday
            date += timedelta(days=1)
        return date
        
    def calculate_order_amount(self, price: float) -> float:
        """计算订单金额"""
        return self.scheduled_investment / price
        
    def on_event(self, event: MarketEvent):
        """处理市场事件"""
        if isinstance(event, ScheduleEvent):
            # 检查是否达到定投日期
            if self.investment_dates and event.timestamp >= self.investment_dates[0]:
                self.investment_dates.popleft()
                order_amount = self.calculate_order_amount(event.price)
                # 检查止损止盈条件
                if self._check_stop_conditions(event.price):
                    return
                # 生成交易信号
                self.generate_signals(order_amount)
                
    def _check_stop_conditions(self, price: float) -> bool:
        """检查止损止盈条件"""
        if self.config.stop_loss is not None:
            current_value = self.current_holdings * price
            if current_value <= self.position_cost * (1 - self.config.stop_loss):
                sell_qty = min(self.current_holdings, 
                             self.current_holdings * self.config.stop_loss_pct)
                self.generate_signals(-sell_qty)  # 部分平仓
                return True
                
        if self.config.take_profit is not None:
            current_value = self.current_holdings * price
            if current_value >= self.position_cost * (1 + self.config.take_profit):
                sell_qty = min(self.current_holdings,
                             self.current_holdings * self.config.take_profit_pct)
                self.generate_signals(-sell_qty)  # 部分平仓
                return True
        return False
                
    def sync_position(self, engine_position: dict):
        """同步引擎仓位到策略"""
        self.position_size = engine_position['quantity']
        self.position_cost = engine_position['avg_price']
        self.current_holdings = self.position_size

    def generate_signals(self, order_amount: float):
        """生成交易信号"""
        # 对于卖出订单，检查持仓是否足够
        if order_amount < 0:
            current_holdings = self.engine.strategy_holdings.get(self.strategy_id, 0)
            if abs(order_amount) > current_holdings:
                order_amount = -current_holdings  # 调整卖出数量为当前持仓
        
        # 生成买入/卖出信号
        signal = {
            'timestamp': datetime.now(),
            'symbol': self.config.target_symbol,
            'quantity': abs(order_amount),  # 确保数量为正
            'price': None,  # 将在执行时确定
            'type': 'buy' if order_amount > 0 else 'sell',
            'strategy_id': self.strategy_id,
            'position_size': self.position_size,
            'position_cost': self.position_cost
        }
        
        # 确保策略ID正确传递到引擎
        if not self.strategy_id:
            raise ValueError("策略ID不能为空")
        
        # 只有数量大于0时才生成信号
        if signal['quantity'] > 0:
            self.signals.append(signal)
            # 触发信号事件
            from ..events import SignalEvent
            signal_event = SignalEvent(
                timestamp=signal['timestamp'],
                signal=signal
            )
            self.push_event(signal_event)
