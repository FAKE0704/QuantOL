from core.strategy.strategy import Strategy
from core.strategy.rule_parser import RuleParser
from event_bus.event_types import SignalEvent
from typing import Optional
import pandas as pd

class RuleBasedStrategy(Strategy):
    """基于规则表达式的策略实现"""
    
    def __init__(self, Data: pd.DataFrame, name: str, rule_expr: str):
        """
        Args:
            Data: 市场数据DataFrame
            name: 策略名称
            rule_expr: 规则表达式字符串
        """
        super().__init__(Data, name)
        self.rule_expr = rule_expr
        self.parser = RuleParser(Data)
        
    def generate_signals(self) -> Optional[SignalEvent]:
        """根据规则表达式生成交易信号"""
        try:
            # 解析规则表达式
            should_buy = self.parser.parse(self.rule_expr)
            
            if should_buy:
                return SignalEvent(
                    symbol=self.Data['symbol'].iloc[-1],
                    signal_type='BUY',
                    strength=1.0,
                    timestamp=pd.Timestamp.now()
                )
            else:
                # 可以添加卖出规则逻辑
                return None
                
        except Exception as e:
            self.logger.error(f"规则解析失败: {str(e)}")
            return None
            
    def on_schedule(self) -> None:
        """定时触发规则检查"""
        signal = self.generate_signals()
        if signal:
            self.emit_signal(signal)
