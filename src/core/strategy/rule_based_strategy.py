
from src.core.strategy.rule_parser import RuleParser
from src.core.strategy.strategy import BaseStrategy
from src.event_bus.event_types import StrategySignalEvent
from src.core.strategy.indicators import IndicatorService
from src.core.strategy.signal_types import SignalType
from typing import Optional, Any
import pandas as pd
from src.support.log.logger import logger

class RuleBasedStrategy(BaseStrategy):
    """基于规则表达式的策略实现"""
    
    def __init__(self, Data: pd.DataFrame, name: str, 
                 indicator_service: IndicatorService,
                 buy_rule_expr: str = "", sell_rule_expr: str = "",
                 open_rule_expr: str = "", close_rule_expr: str = "",
                 portfolio_manager: Any = None):
        """
        Args:
            Data: 市场数据DataFrame
            name: 策略名称
            indicator_service: 指标计算服务
            buy_rule_expr: 加仓规则表达式字符串
            sell_rule_expr: 平仓规则表达式字符串
            open_rule_expr: 开仓规则表达式字符串
            close_rule_expr: 清仓规则表达式字符串
        """
        super().__init__(Data, name)
        self.buy_rule_expr = buy_rule_expr
        self.sell_rule_expr = sell_rule_expr
        self.open_rule_expr = open_rule_expr
        self.close_rule_expr = close_rule_expr
        self.portfolio_manager = portfolio_manager
        self.parser = RuleParser(Data, indicator_service, portfolio_manager)

    def copy_for_symbol(self, symbol: str):
        """为指定符号创建策略副本"""
        # 创建新的策略实例，保持相同的规则表达式
        return RuleBasedStrategy(
            Data=self.Data,  # 注意：这里需要传入对应符号的数据
            name=f"{self.name}_{symbol}",
            indicator_service=self.indicator_service,
            buy_rule_expr=self.buy_rule_expr,
            sell_rule_expr=self.sell_rule_expr,
            open_rule_expr=self.open_rule_expr,
            close_rule_expr=self.close_rule_expr,
            portfolio_manager=self.portfolio_manager
        )
        
    def _generate_signal_from_rule(self, rule_expr: str, signal_type: SignalType, rule_type: str) -> Optional[StrategySignalEvent]:
        """根据规则表达式生成交易信号（统一处理函数）
        Args:
            rule_expr: 规则表达式
            signal_type: 信号类型
            rule_type: 规则类型（用于日志记录）
        Returns:
            交易信号事件或None
        """
        if not rule_expr:
            return None
            
        try:
            should_trade = self.parser.parse(rule_expr)
            # logger.debug(f"{rule_type}规则解析结果: {should_trade}")
            if should_trade:
                # logger.debug(f"生成 {signal_type.value} 信号")
                return StrategySignalEvent(
                    strategy_id=self.strategy_id,
                    symbol=self.Data['code'].iloc[-1],
                    signal_type=signal_type,
                    price=float(self.Data.loc[self.parser.current_index,'close']),
                    quantity=100,  # 默认数量
                    confidence=1.0,
                    timestamp=self.Data.loc[self.parser.current_index,'combined_time'],
                    parameters={'current_index': self.parser.current_index}
                )
        except Exception as e:
            logger.error(f"{rule_type}规则解析失败: {str(e)}")
        return None

    def generate_signals(self, current_index: int) -> Optional[StrategySignalEvent]:
        """根据开仓/清仓/加仓/平仓规则表达式生成交易信号
        Args:
            current_index: 当前数据索引位置
        """
        try:           
            # 更新解析器数据为最新数据
            self.parser.data = self.Data
            self.parser.current_index = current_index
            
            # 首先评估所有规则以确保列生成（即使不触发信号也要评估）
            all_rules = [
                (self.open_rule_expr, SignalType.OPEN, '开仓'),
                (self.close_rule_expr, SignalType.CLOSE, '清仓'), 
                (self.buy_rule_expr, SignalType.BUY, '加仓'),
                (self.sell_rule_expr, SignalType.SELL, '平仓')
            ]
            
            # 评估所有规则以确保列生成
            for rule_expr, signal_type, rule_type in all_rules:
                if rule_expr:
                    try:
                        # 评估规则但不生成信号（仅用于列生成）
                        self.parser.parse(rule_expr)
                    except Exception as e:
                        logger.error(f"{rule_type}规则评估失败（列生成）: {str(e)}")
            
            # 按优先级顺序检查规则：开仓 > 清仓 > 加仓 > 平仓 （原代码：出现信号即跳出，会导致某些规则没有被解析评估）
            signal = self._generate_signal_from_rule(self.open_rule_expr, SignalType.OPEN, '开仓')
            if signal:
                return signal
                
            signal = self._generate_signal_from_rule(self.close_rule_expr, SignalType.CLOSE, '清仓')
            if signal:
                return signal
                
            signal = self._generate_signal_from_rule(self.buy_rule_expr, SignalType.BUY, '加仓')
            if signal:
                return signal
                
            signal = self._generate_signal_from_rule(self.sell_rule_expr, SignalType.SELL, '平仓')
            if signal:
                return signal
            
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

