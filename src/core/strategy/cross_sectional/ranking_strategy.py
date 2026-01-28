"""基于横截面排名的策略模块"""
import pandas as pd
from datetime import datetime
from typing import Dict, List, Any, Optional
from uuid import uuid4

from src.core.strategy.strategy import BaseStrategy
from src.core.strategy.cross_sectional.ranking_service import CrossSectionalRankingService
from src.event_bus.event_types import StrategySignalEvent
from src.core.strategy.signal_types import SignalType
from src.support.log.logger import logger
from src.core.portfolio.portfolio_interface import Position


class RankingBasedStrategy(BaseStrategy):
    """基于横截面排名的策略

    通过横截面排名选择标的，并在再平衡时点进行调仓。
    """

    def __init__(
        self,
        data_dict: Dict[str, pd.DataFrame],
        name: str,
        ranking_service: CrossSectionalRankingService,
        portfolio_manager: Any = None,
        indicator_service: Any = None
    ):
        """

        Args:
            data_dict: 所有标的的市场数据字典
            name: 策略名称
            ranking_service: 横截面排名服务
            portfolio_manager: 投资组合管理器
            indicator_service: 指标计算服务
        """
        # 使用第一个标的的数据初始化基类（兼容性）
        first_symbol = next(iter(data_dict.keys()))
        super().__init__(data_dict[first_symbol], name)

        self.data_dict = data_dict
        self.ranking_service = ranking_service
        self.portfolio_manager = portfolio_manager
        self.indicator_service = indicator_service

        self.current_positions: set = set()  # 当前持仓标的集合
        self.target_positions: set = set()  # 目标持仓标的集合
        self.last_rebalance_date: Optional[pd.Timestamp] = None
        self.last_ranking: Optional[pd.DataFrame] = None

        logger.info(f"初始化基于排名的策略: {name}")

    def should_rebalance(self, timestamp: pd.Timestamp) -> bool:
        """判断是否需要再平衡

        Args:
            timestamp: 当前时间

        Returns:
            是否需要再平衡
        """
        return self.ranking_service.should_rebalance(timestamp, self.last_rebalance_date)

    def calculate_signals(
        self,
        timestamp: pd.Timestamp,
        current_prices: Dict[str, float]
    ) -> List[StrategySignalEvent]:
        """计算再平衡信号

        Args:
            timestamp: 当前时间
            current_prices: 各标的当前价格 {symbol: price}

        Returns:
            策略信号事件列表
        """
        signals = []

        # 检查是否需要再平衡
        if not self.should_rebalance(timestamp):
            return signals

        logger.info(f"开始计算再平衡信号，时间: {timestamp}")

        # 计算横截面因子
        factor_values = self.ranking_service.calculate_cross_sectional_factor(
            data_dict=self.data_dict,
            timestamp=timestamp,
            portfolio_manager=self.portfolio_manager
        )

        # 应用过滤条件
        filtered_values = self.ranking_service.apply_filters(
            data_dict=self.data_dict,
            timestamp=timestamp,
            factor_values=factor_values
        )

        # 排名
        ranking_df = self.ranking_service.rank_symbols(filtered_values)
        self.last_ranking = ranking_df

        # 获取目标标的列表
        target_symbols = self.ranking_service.get_selected_symbols(ranking_df)
        self.target_positions = set(target_symbols)

        # 获取仓位权重
        position_weights = self.ranking_service.get_position_weights(target_symbols)

        # 更新当前持仓集合
        self._update_current_positions()

        # 生成卖出信号（卖出不在目标列表中的持仓）
        for symbol in self.current_positions:
            if symbol not in self.target_positions:
                price = current_prices.get(symbol)
                if price and price > 0:
                    signal = self._create_sell_signal(symbol, price, timestamp)
                    signals.append(signal)
                    logger.info(f"生成卖出信号: {symbol} @ {price}")

        # 生成买入信号（买入目标列表中未持仓的标的）
        for symbol in self.target_positions:
            if symbol not in self.current_positions:
                price = current_prices.get(symbol)
                if price and price > 0:
                    weight = position_weights.get(symbol, 0.1)
                    signal = self._create_buy_signal(symbol, price, timestamp, weight)
                    signals.append(signal)
                    logger.info(f"生成买入信号: {symbol} @ {price}, 权重: {weight}")

        # 更新再平衡日期
        self.last_rebalance_date = timestamp
        logger.info(f"再平衡信号生成完成，共生成 {len(signals)} 个信号")

        return signals

    def _update_current_positions(self):
        """更新当前持仓集合"""
        if not self.portfolio_manager:
            return

        self.current_positions.clear()

        # 获取所有持仓
        all_positions = self.portfolio_manager.get_all_positions()
        for symbol, position in all_positions.items():
            if position and position.quantity != 0:
                self.current_positions.add(symbol)

        logger.debug(f"当前持仓标的: {self.current_positions}")

    def _create_buy_signal(
        self,
        symbol: str,
        price: float,
        timestamp: pd.Timestamp,
        weight: float
    ) -> StrategySignalEvent:
        """创建买入信号

        Args:
            symbol: 标的代码
            price: 价格
            timestamp: 时间戳
            weight: 目标仓位权重

        Returns:
            策略信号事件
        """
        event = StrategySignalEvent(
            timestamp=datetime.now(),
            strategy_id=self.strategy_id,
            symbol=symbol,
            signal_type=SignalType.REBALANCE,
            price=price,
            quantity=0,  # 让系统自动计算
            confidence=1.0,
            engine=None,
            parameters={"weight": weight},
            position_percent=weight
        )
        # 设置event_type（BaseEvent要求的属性）
        event.event_type = "STRATEGY_SIGNAL"
        return event

    def _create_sell_signal(
        self,
        symbol: str,
        price: float,
        timestamp: pd.Timestamp
    ) -> StrategySignalEvent:
        """创建卖出信号

        Args:
            symbol: 标的代码
            price: 价格
            timestamp: 时间戳

        Returns:
            策略信号事件
        """
        # 获取当前持仓数量
        quantity = 0
        if self.portfolio_manager:
            position = self.portfolio_manager.get_position(symbol)
            if position:
                quantity = abs(position.quantity)

        event = StrategySignalEvent(
            timestamp=datetime.now(),
            strategy_id=self.strategy_id,
            symbol=symbol,
            signal_type=SignalType.CLOSE,
            price=price,
            quantity=int(quantity),
            confidence=1.0,
            engine=None,
            parameters={"reason": "not_in_target_list"}
        )
        # 设置event_type（BaseEvent要求的属性）
        event.event_type = "STRATEGY_SIGNAL"
        return event

    def get_current_target_positions(self) -> set:
        """获取当前目标持仓集合"""
        return self.target_positions.copy()

    def get_current_positions(self) -> set:
        """获取当前实际持仓集合"""
        self._update_current_positions()
        return self.current_positions.copy()

    def get_last_ranking(self) -> Optional[pd.DataFrame]:
        """获取最后一次排名结果"""
        return self.last_ranking

    def handle_event(self, engine, event):
        """处理事件（基类方法实现）"""
        # 基于排名的策略通常不需要响应定时事件
        # 再平衡由外部通过calculate_signals方法触发
        pass
