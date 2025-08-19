from typing import Any, Dict, Optional
from event_bus.event_types import StrategySignalEvent, StrategyScheduleEvent

def handle_signal(event: StrategySignalEvent):
    """处理策略信号事件"""
    try:
        # 执行策略计算
        if not event.engine or not hasattr(event.engine, 'strategy'):
            return False
        signals = event.engine.strategy.calculate_signals(
            getattr(event.engine, 'market_data', None),
            event.parameters or {}
        )
        
        # 生成交易信号
        for signal in signals:
            event.engine.create_order(
                event.timestamp,
                symbol=signal['symbol'],
                quantity=signal['quantity'],
                side=signal['side'],
                price=signal['price'],
                strategy_id=getattr(getattr(event.engine, 'current_strategy', None), 'strategy_id', None)
            )
        return True
    except Exception as e:
        event.engine.log_error(f"策略计算失败: {str(e)}")
        return False

def handle_schedule(event: StrategyScheduleEvent):
    """处理定时任务事件"""
    if event.schedule_type == "MONTHLY":
        # 执行定投买入
        amount = event.parameters.get("investment_amount", 0)
        if amount <= 0:
            return False
            
        if not event.engine:
            return False
        price = event.engine.current_price
        quantity = int(amount / price)
        if quantity <= 0:
            return False
            
        if not event.engine or not hasattr(event.engine, 'config'):
            return False
        event.engine.create_order(
            event.timestamp,
            symbol=getattr(event.engine.config, 'target_symbol', ''),
            quantity=quantity,
            side="BUY",
            price=price,
            strategy_id=event.parameters.get("strategy_id")
        )
        return True
        
    try:
        # 加载历史数据
        if not event.engine:
            return False
        data = event.engine.get_historical_data(
            event.timestamp, 
            lookback_days=event.parameters.get('lookback_days', 30)
        )
        return True
    except Exception as e:
        if event.engine and hasattr(event.engine, 'log_error'):
            event.engine.log_error(f"加载历史数据失败: {str(e)}")
        return False
