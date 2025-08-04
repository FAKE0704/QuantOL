from event_bus.event_types import (
    MarketDataEvent, 
    OrderEvent,
    StrategySignalEvent,
    StrategyScheduleEvent
)

class StrategyEventAdapter:
    """策略事件适配器（将策略领域事件转换为通用事件）"""
    
    @staticmethod
    def convert_signal(signal_event: SignalEvent) -> OrderEvent:
        """将策略信号事件转换为通用订单事件"""
        return OrderEvent(
            timestamp=signal_event.timestamp,
            symbol=signal_event.symbol,
            quantity=signal_event.quantity,
            side=signal_event.side,
            price=signal_event.price,
            strategy_id=signal_event.strategy_id
        )
    
    @staticmethod
    def convert_schedule(schedule_event: ScheduleEvent) -> MarketDataEvent:
        """将定时任务事件转换为市场数据事件"""
        return MarketDataEvent(
            timestamp=schedule_event.timestamp,
            symbol=schedule_event.symbol,
            data_type=schedule_event.schedule_type,
            data=schedule_event.parameters
        )

def handle_signal(event: SignalEvent):
    """处理策略信号事件（迁移自原event_handlers）"""
    try:
        # 直接使用信号事件字段构造订单
        order_event = StrategyEventAdapter.convert_signal(event)
        event.engine.event_bus.publish("order_events", order_event)
        return True
    except Exception as e:
        event.engine.log_error(f"策略计算失败: {str(e)}")
        return False

def handle_schedule(event: ScheduleEvent):
    """处理定时任务事件（迁移自原event_handlers）"""
    if event.schedule_type == "FIXED_INVEST":
        # 使用适配器转换为市场数据事件
        market_data_event = StrategyEventAdapter.convert_schedule(event)
        event.engine.event_bus.publish("market_data_events", market_data_event)
        return True
        
    try:
        # 加载历史数据
        data = event.engine.get_historical_data(
            event.timestamp, 
            lookback_days=30  # 默认30天
        )
        return True
    except Exception as e:
        event.engine.log_error(f"加载历史数据失败: {str(e)}")
        return False
