
from core.strategy.rule_parser import RuleParser
from core.strategy.strategy import BaseStrategy
from event_bus.event_types import StrategySignalEvent
from core.strategy.indicators import IndicatorService
from typing import Optional
import pandas as pd
from support.log.logger import logger

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
        
    def generate_signals(self, current_index: int) -> Optional[StrategySignalEvent]:
        """根据买入/卖出规则表达式生成交易信号
        Args:
            current_index: 当前数据索引位置
        """
        try:           
            # 更新解析器数据为最新数据
            self.parser.data = self.Data
            
            if not self.Data.empty:
                last_row = self.Data.iloc[-1]
                
                # 记录关键指标值
                # logger.debug("当前技术指标值: %s", 
                #     {k: v for k,v in last_row.items() 
                #      if k in ['ma5', 'ma10', 'macd', 'rsi', 'kdj_k', 'kdj_d']})
            
            # 解析买入规则
            if self.buy_rule_expr:
                should_buy = self.parser.parse(self.buy_rule_expr)
                # logger.debug(f"买入规则解析结果: {should_buy}")
                if should_buy:
                    # logger.debug("生成 BUY 信号")
                    return StrategySignalEvent(
                        strategy_id=self.strategy_id,
                        symbol=self.Data['code'].iloc[-1],
                        direction='BUY',
                        price=float(self.Data.loc[self.parser.current_index,'close']),
                        quantity=100,  # 默认数量，实际不使用
                        confidence=1.0,
                        timestamp=self.Data.loc[current_index,'combined_time'],
                        parameters={'current_index': current_index}
                    )
            
            # 解析卖出规则
            if self.sell_rule_expr:
                should_sell = self.parser.parse(self.sell_rule_expr)
                # logger.debug(f"卖出规则解析结果: {should_sell}")
                if should_sell:
                    # logger.debug("生成 SELL 信号")
                    return StrategySignalEvent(
                        strategy_id=self.strategy_id,
                        symbol=self.Data['code'].iloc[-1],
                        direction='SELL',
                        price=float(self.Data.loc[self.parser.current_index,'close']),
                        quantity=100,  # 默认数量
                        confidence=1.0,
                        timestamp=self.Data.loc[current_index,'combined_time'],
                        parameters={'current_index': current_index}
                    )
            
            
            return None
                
        except Exception as e:
            logger.error(f"规则解析失败: {str(e)}", exc_info=True)
            return None
        finally:
            # 每次调用后清理缓存
            self.parser.clear_cache()
            
    def on_schedule(self, engine) -> None:
        """定时触发规则检查"""
        
        # 同步当前索引到规则解析器
        self.parser.current_index = engine.current_index
        signal = self.generate_signals(engine.current_index)
        if signal:
        #    logger.debug(f"当前信号事件的close:{signal.price}")
           engine._handle_signal_event(signal)

