from event_bus.event_types import (
    MarketDataEvent, 
    OrderEvent,
    StrategySignalEvent,
    StrategyScheduleEvent,
    FillEvent
)
from core.risk.risk_manager import RiskManager
import random
from datetime import datetime

class StrategyEventHandler:
    """策略事件处理器（专为StrategySignalEvent设计）"""
    
    @staticmethod
    def handle_strategy_signal(event: StrategySignalEvent):
        """处理策略信号事件"""
        # 转换为通用订单事件（根据OrderEvent定义调整）
        order_event = OrderEvent(
            strategy_id=event.strategy_id,
            symbol=event.symbol,
            direction=event.direction,
            price=event.price,
            quantity=event.quantity,
            order_type="LIMIT"
        )
        
        # 风险管理检查
        risk_manager = RiskManager(event.engine.portfolio)
        if not risk_manager.validate_order(order_event):
            event.engine.log_warning(f"订单被风险管理系统拒绝: {order_event}")
            return None
        
        # 处理订单并返回FillEvent
        fill_event = handle_order(order_event, event.engine)
        return fill_event
    
    @staticmethod
    def convert_schedule(schedule_event: StrategyScheduleEvent) -> MarketDataEvent:
        """将定时任务事件转换为市场数据事件"""
        return MarketDataEvent(
            symbol=schedule_event.symbol,
            price=0,  # 实际价格需要根据策略计算
            volume=0,  # 实际交易量需要根据策略计算
            timestamp=schedule_event.timestamp,
            exchange="SH"  # 默认上交所
        )

def handle_order(order_event: OrderEvent, engine):
    """处理订单事件（生成FillEvent）"""
    try:
        # 回测环境模拟成交
        if engine.is_backtesting:
            # 模拟滑点（±0.5%）
            slippage = random.uniform(-0.005, 0.005)
            fill_price = order_event.price * (1 + slippage)
            
            # 模拟手续费（0.1%）
            commission = fill_price * order_event.quantity * 0.001
            
            fill_event = FillEvent(
                order_id=f"order_{datetime.now().timestamp()}",
                symbol=order_event.symbol,
                fill_price=fill_price,
                fill_quantity=order_event.quantity,
                commission=commission,
                timestamp=datetime.now()
            )
            return fill_event
        
        # 实盘环境执行真实交易
        from core.execution.Trader import LiveTrader
        trader = LiveTrader(engine.api_config)
        return trader.execute_order(order_event)
        
    except Exception as e:
        engine.log_error(f"订单执行失败: {str(e)}")
        return None

def handle_schedule(event: StrategyScheduleEvent):
    """处理策略定时任务事件"""
    if event.schedule_type == "FIXED_INVEST":
        # 使用适配器转换为市场数据事件
        market_data_event = StrategyEventHandler.convert_schedule(event)
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
