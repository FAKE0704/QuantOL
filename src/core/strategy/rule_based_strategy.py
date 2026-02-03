
from src.core.strategy.rule_parser import RuleParser
from src.core.strategy.strategy import BaseStrategy
from src.event_bus.event_types import StrategySignalEvent
from src.core.strategy.indicators import IndicatorService
from src.core.strategy.signal_types import SignalType
from typing import Optional, Any, Dict
import pandas as pd
from src.support.log.logger import logger

class RuleBasedStrategy(BaseStrategy):
    """基于规则表达式的策略实现"""
    
    def __init__(self, Data: pd.DataFrame, name: str,
                 indicator_service: IndicatorService,
                 buy_rule_expr: str = "", sell_rule_expr: str = "",
                 open_rule_expr: str = "", close_rule_expr: str = "",
                 portfolio_manager: Any = None,
                 cross_sectional_context: Optional[Dict[str, Any]] = None):
        """
        Args:
            Data: 市场数据DataFrame
            name: 策略名称
            indicator_service: 指标计算服务
            buy_rule_expr: 加仓规则表达式字符串
            sell_rule_expr: 平仓规则表达式字符串
            open_rule_expr: 开仓规则表达式字符串
            close_rule_expr: 清仓规则表达式字符串
            portfolio_manager: 投资组合管理器
            cross_sectional_context: 横截面上下文（用于RANK函数）
        """
        super().__init__(Data, name)
        self.buy_rule_expr = buy_rule_expr
        self.sell_rule_expr = sell_rule_expr
        self.open_rule_expr = open_rule_expr
        self.close_rule_expr = close_rule_expr
        self.portfolio_manager = portfolio_manager
        self.parser = RuleParser(Data, indicator_service, portfolio_manager, cross_sectional_context)
        self.debug_data = Data.copy()  # 初始化时保存原始数据

        # 在初始化时完整评估所有规则以生成规则列
        self._initialize_rule_columns()

        # 调试：验证数据对象关系
        logger.info(f"策略初始化完成 - Data地址: {id(self.Data)}, parser.data地址: {id(self.parser.data)}, 是否同一对象: {id(self.Data) == id(self.parser.data)}")
        logger.info(f"              debug_data地址: {id(self.debug_data)}, 与parser.data同一: {id(self.debug_data) == id(self.parser.data)}")

    def _initialize_rule_columns(self):
        """初始化规则列：完整评估所有规则以生成所有数据点的结果"""
        try:
            all_rules = [
                (self.open_rule_expr, '开仓'),
                (self.close_rule_expr, '清仓'),
                (self.buy_rule_expr, '加仓'),
                (self.sell_rule_expr, '平仓')
            ]

            for rule_expr, rule_type in all_rules:
                if rule_expr:
                    logger.info(f"开始初始化{rule_type}规则: {rule_expr}")
                    try:
                        # 完整评估规则以生成所有数据点的结果
                        for i in range(len(self.Data)):
                            self.parser.current_index = i
                            should_trade = self.parser.parse(rule_expr, mode='rule')
                            # 每1000行记录一次进度
                            if i % 1000 == 0:
                                logger.info(f"{rule_type}规则评估进度: {i}/{len(self.Data)}")
                            if i < 5:  # 只记录前5个索引的结果
                                logger.debug(f"{rule_type}规则[{i}]: {should_trade}")

                        clean_rule = self.parser._clean_rule_name(rule_expr)
                        if clean_rule in self.parser.data.columns:
                            true_count = self.parser.data[clean_rule].sum()
                            logger.info(f"{rule_type}规则初始化完成，{clean_rule}列中有 {true_count} 个True值")

                        # 检查SMA列是否存在
                        sma_col = f"SMA(close,5)"
                        if sma_col in self.parser.data.columns:
                            non_null = self.parser.data[sma_col].notna().sum()
                            logger.info(f"SMA列统计: 总行数={len(self.parser.data)}, 非空值={non_null}, 前5个值={self.parser.data[sma_col].head().tolist()}")

                    except Exception as e:
                        logger.error(f"{rule_type}规则完整评估失败: {str(e)}")

            # 初始化完成后，保存debug_data
            self.debug_data = self.parser.data.copy()

            # 保存规则类型映射到 attrs 中，供前端使用
            if not hasattr(self.debug_data, 'attrs'):
                self.debug_data.attrs = {}
            self.debug_data.attrs['rule_type_mapping'] = {}
            for rule_expr, rule_type in all_rules:
                if rule_expr:
                    clean_rule = self.parser._clean_rule_name(rule_expr)
                    self.debug_data.attrs['rule_type_mapping'][clean_rule] = rule_type

            logger.info(f"规则列初始化完成，总列数: {len(self.debug_data.columns)}")
            logger.info(f"规则类型映射: {self.debug_data.attrs['rule_type_mapping']}")

        except Exception as e:
            logger.error(f"规则列初始化失败: {str(e)}")
            raise

    # _evaluate_rule_complete方法已删除，因为规则评估现在在初始化时完成

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

        注意：使用初始化时保存的规则列值，确保展示和交易逻辑一致
        """
        if not rule_expr:
            return None

        try:
            clean_rule = self.parser._clean_rule_name(rule_expr)

            # 检查规则是否包含 COST 或 POSITION 变量
            # 如果包含，需要实时解析（因为这些变量在回测过程中会变化）
            has_dynamic_vars = 'COST' in rule_expr or 'POSITION' in rule_expr

            if has_dynamic_vars:
                # 实时解析包含动态变量的规则
                should_trade = self.parser.parse(rule_expr, mode='rule')
            elif clean_rule in self.parser.data.columns:
                # 使用初始化时保存的规则列值（不重新解析，确保一致性）
                should_trade = bool(self.parser.data.at[self.parser.current_index, clean_rule])
            else:
                # 规则列不存在的fallback情况（不应该发生）
                logger.warning(f"{rule_type}规则列[{clean_rule}]不存在于parser.data")
                should_trade = self.parser.parse(rule_expr)

            if should_trade:
                logger.info(f"{rule_type}规则触发！生成 {signal_type.value} 信号")
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
            # 确保parser使用的是正确的数据引用
            if id(self.parser.data) != id(self.Data):
                logger.warning("parser.data和self.Data不是同一个对象，重新设置")
                self.parser.data = self.Data.copy()

            # 更新解析器当前索引
            self.parser.current_index = current_index

            # 获取当前标的的持仓状态
            current_symbol = self.Data['code'].iloc[-1] if 'code' in self.Data.columns else None
            current_position = 0
            if self.portfolio_manager and current_symbol:
                position = self.portfolio_manager.get_position(current_symbol)
                current_position = position.quantity if position else 0

            # 根据持仓状态决定检查哪些规则
            if current_position == 0:
                # 无持仓：只检查开仓规则
                signal = self._generate_signal_from_rule(self.open_rule_expr, SignalType.OPEN, '开仓')
                if signal:
                    logger.info(f"生成开仓信号: {signal}")
                    return signal
            else:
                # 有持仓：检查清仓、加仓、平仓规则（按优先级）

                # 优先检查清仓规则（完全退出）
                signal = self._generate_signal_from_rule(self.close_rule_expr, SignalType.LIQUIDATE, '清仓')
                if signal:
                    logger.info(f"生成清仓信号: {signal}")
                    return signal

                # 其次检查平仓规则（部分退出）
                signal = self._generate_signal_from_rule(self.sell_rule_expr, SignalType.SELL, '平仓')
                if signal:
                    logger.info(f"生成平仓信号: {signal}")
                    return signal

                # 最后检查加仓规则
                signal = self._generate_signal_from_rule(self.buy_rule_expr, SignalType.BUY, '加仓')
                if signal:
                    logger.info(f"生成加仓信号: {signal}")
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
            logger.info(f"处理信号事件: {signal}")
            engine._handle_signal_event(signal)

