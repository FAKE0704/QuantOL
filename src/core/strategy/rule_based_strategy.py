
from core.strategy.rule_parser import RuleParser
from core.strategy.strategy import BaseStrategy
from event_bus.event_types import SignalEvent
from core.strategy.indicators import IndicatorService
from typing import Optional
import pandas as pd

class RuleBasedStrategy(BaseStrategy):
    """基于规则表达式的策略实现"""
    
    def __init__(self, Data: pd.DataFrame, name: str, 
                 indicator_service: IndicatorService,
                 buy_rule_expr: str = "", sell_rule_expr: str = ""):
        """
        Args:
            Data: 市场数据DataFrame
            name: 策略名称
            indicator_service: 指标计算服务
            buy_rule_expr: 买入规则表达式字符串
            sell_rule_expr: 卖出规则表达式字符串
        """
        super().__init__(Data, name)
        self.buy_rule_expr = buy_rule_expr
        self.sell_rule_expr = sell_rule_expr
        self.parser = RuleParser(Data, indicator_service)
        
    def generate_signals(self) -> Optional[SignalEvent]:
        """根据买入/卖出规则表达式生成交易信号"""
        try:
            # 更新解析器数据为最新数据
            self.parser.data = self.Data
            
            # 解析买入规则
            if self.buy_rule_expr:
                should_buy = self.parser.parse(self.buy_rule_expr)
                if should_buy:
                    return SignalEvent(
                        strategy_id=self.strategy_id,
                        symbol=self.Data['symbol'].iloc[-1],
                        signal_type='BUY',
                        strength=1.0,
                        timestamp=pd.Timestamp.now()
                    )
            
            # 解析卖出规则
            if self.sell_rule_expr:
                should_sell = self.parser.parse(self.sell_rule_expr)
                if should_sell:
                    return SignalEvent(
                        strategy_id=self.strategy_id,
                        symbol=self.Data['symbol'].iloc[-1],
                        signal_type='SELL',
                        strength=1.0,
                        timestamp=pd.Timestamp.now()
                    )
            
            return None
                
        except Exception as e:
            self.logger.error(f"规则解析失败: {str(e)}")
            return None
        finally:
            # 每次调用后清理缓存
            self.parser.clear_cache()
            
    def on_schedule(self) -> None:
        """定时触发规则检查"""
        signal = self.generate_signals()
        if signal:
            # 通过引擎创建订单
            self.engine.create_order(
                pd.Timestamp.now(),
                symbol=self.Data['symbol'].iloc[-1],
                quantity=100,  # 默认数量
                side=signal.signal_type,
                price=float(self.Data['close'].iloc[-1]),
                strategy_id=self.strategy_id
            )
