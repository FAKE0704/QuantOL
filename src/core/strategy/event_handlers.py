from core.strategy.events import ScheduleEvent, SignalEvent



def handle_signal(event: SignalEvent):
    """处理策略信号事件"""
    try:
        # 执行策略计算
        signals = event.engine.strategy.calculate_signals(
            event.engine.market_data,
            event.parameters
        )
        
        # 生成交易信号
        for signal in signals:
            event.engine.create_order(
                event.timestamp,
                symbol=signal['symbol'],
                quantity=signal['quantity'],
                side=signal['side'],
                price=signal['price'],
                strategy_id=event.engine.current_strategy.strategy_id
            )
        return True
    except Exception as e:
        event.engine.log_error(f"策略计算失败: {str(e)}")
        return False

def handle_schedule(event: ScheduleEvent):
    """处理定时任务事件"""
    if event.schedule_type == "FIXED_INVEST":
        # 执行定投买入
        amount = event.parameters["amount"]
        price = event.engine.market_data.iloc[-1]["close"]
        quantity = amount / price
        event.engine.create_order(
            event.timestamp,
            symbol=event.engine.config.target_symbol,
            quantity=quantity,
            side="BUY",
            price=price
        )
        return True
        
    try:
        # 加载历史数据
        data = event.engine.get_historical_data(
            event.timestamp, 
            lookback_days=event.parameters.get('lookback_days', 30)
        )
        return True
    except Exception as e:
        event.engine.log_error(f"加载历史数据失败: {str(e)}")
        return False
