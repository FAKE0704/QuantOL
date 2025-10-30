"""
固定比例仓位管理策略

根据设计文档 docs/strategies/fixed_percent_position_strategy.md 实现
"""

import logging
from typing import Dict, Any, Optional
from src.core.strategy.signal_types import SignalType

logger = logging.getLogger(__name__)

class FixedPercentPositionStrategy:
    """
    固定比例仓位管理策略

    核心原则：
    - 基于初始资金或当前可用资金的固定比例进行交易
    - 开仓信号：按固定比例开仓（仅当无持仓时）
    - 加仓信号：按固定比例增加仓位
    - 平仓信号：按固定比例部分卖出（不是完全平仓）
    - 清仓信号：完全清仓所有仓位
    """

    def __init__(self, percent: float = 0.1, use_initial_capital: bool = True, min_lot_size: int = 100):
        """
        初始化固定比例仓位策略

        Args:
            percent: 仓位比例（0-1之间）
            use_initial_capital: 是否基于初始资金计算（True）或当前权益（False）
            min_lot_size: 最小交易手数
        """
        if not 0 < percent <= 1:
            raise ValueError("仓位比例必须在0到1之间")

        self.percent = percent
        self.use_initial_capital = use_initial_capital
        self.min_lot_size = min_lot_size

    def calculate_position_size(self, signal_type: SignalType, portfolio_data: Dict[str, float],
                             current_price: float, current_position: int = 0) -> int:
        """
        计算目标仓位大小

        Args:
            signal_type: 信号类型（OPEN, ADD, CLOSE, LIQUIDATE）
            portfolio_data: 投资组合数据
                - initial_capital: 初始资金
                - available_cash: 可用现金
                - total_equity: 总权益
            current_price: 当前价格
            current_position: 当前持仓数量

        Returns:
            int: 目标交易数量（正数买入，负数卖出，0表示无操作）
        """

        try:
            if signal_type == SignalType.LIQUIDATE:
                return self._calculate_liquidate_position_size(current_position)

            if signal_type == SignalType.CLOSE:
                return -self._calculate_close_position_size(current_position)

            # 计算可用资金
            available_capital = self._get_available_capital(portfolio_data)

            if signal_type == SignalType.OPEN:
                return self._calculate_open_position_size(
                    portfolio_data['available_cash'], current_price, current_position
                )
            elif signal_type == SignalType.ADD:
                return self._calculate_add_position_size(
                    portfolio_data['available_cash'], current_price
                )
            elif signal_type in [SignalType.BUY, SignalType.SELL]:
                # 对于通用买卖信号，根据当前持仓状态决定操作
                if current_position > 0:
                    # 有持仓时，BUY信号作为加仓处理
                    if signal_type == SignalType.BUY:
                        return self._calculate_add_position_size(
                            portfolio_data['available_cash'], current_price
                        )
                    else:  # SELL
                        return -self._calculate_close_position_size(current_position)
                else:
                    # 无持仓时，只有BUY信号可以开仓
                    if signal_type == SignalType.BUY:
                        return self._calculate_open_position_size(
                            portfolio_data['available_cash'], current_price, current_position
                        )
                    else:
                        return 0

            return 0

        except Exception as e:
            logger.error(f"计算仓位大小失败: {str(e)}")
            return 0

    def _get_available_capital(self, portfolio_data: Dict[str, float]) -> float:
        """获取可用资金"""
        if self.use_initial_capital:
            return portfolio_data.get('initial_capital', portfolio_data.get('available_cash', 0))
        else:
            return portfolio_data.get('available_cash', 0)

    def _calculate_open_position_size(self, available_cash: float, current_price: float,
                                   current_position: int) -> int:
        """计算开仓数量（方案C：基于可用资金和持仓状态）"""
        # 已有持仓时不开新仓，避免重复开仓
        if current_position > 0:
            return 0

        # 基于可用现金计算可买数量
        position_value = available_cash * self.percent
        quantity = int(position_value / current_price / self.min_lot_size) * self.min_lot_size

        # 检查资金是否足够
        required_cash = quantity * current_price
        if required_cash > available_cash:
            # 资金不足时减少数量
            quantity = int(available_cash / current_price / self.min_lot_size) * self.min_lot_size

        if quantity > 0:
            logger.debug(f"开仓计算: 可用资金={available_cash}, 价格={current_price}, 数量={quantity}")

        return quantity

    def _calculate_add_position_size(self, available_cash: float, current_price: float) -> int:
        """计算加仓数量"""
        # 加仓时按固定比例计算
        position_value = available_cash * self.percent
        additional_quantity = int(position_value / current_price / self.min_lot_size) * self.min_lot_size

        # 检查资金是否足够
        required_cash = additional_quantity * current_price
        if required_cash > available_cash:
            additional_quantity = int(available_cash / current_price / self.min_lot_size) * self.min_lot_size

        if additional_quantity > 0:
            logger.debug(f"加仓计算: 可用资金={available_cash}, 价格={current_price}, 数量={additional_quantity}")

        return additional_quantity

    def _calculate_close_position_size(self, current_position: int) -> int:
        """计算平仓数量（按固定比例部分卖出）"""
        if current_position <= 0:
            return 0

        # 计算要卖出的数量（按比例）
        sell_quantity = int(current_position * self.percent / self.min_lot_size) * self.min_lot_size

        # 确保不超过当前持仓
        sell_quantity = min(sell_quantity, current_position)

        if sell_quantity > 0:
            logger.debug(f"平仓计算: 当前持仓={current_position}, 卖出数量={sell_quantity}")

        return sell_quantity

    def _calculate_liquidate_position_size(self, current_position: int) -> int:
        """计算清仓数量（完全清仓）"""
        liquidate_quantity = current_position if current_position > 0 else 0

        if liquidate_quantity > 0:
            logger.debug(f"清仓计算: 当前持仓={current_position}, 清仓数量={liquidate_quantity}")

        return liquidate_quantity

    def get_strategy_info(self) -> Dict[str, Any]:
        """获取策略信息"""
        return {
            "strategy_type": "fixed_percent",
            "percent": self.percent,
            "use_initial_capital": self.use_initial_capital,
            "min_lot_size": self.min_lot_size
        }

    def update_parameters(self, **kwargs):
        """更新策略参数"""
        for key, value in kwargs.items():
            if hasattr(self, key):
                if key == "percent":
                    if not 0 < value <= 1:
                        raise ValueError("仓位比例必须在0到1之间")
                elif key == "min_lot_size":
                    if value <= 0:
                        raise ValueError("最小交易手数必须大于0")
                setattr(self, key, value)
                logger.info(f"更新策略参数 {key}: {value}")
            else:
                logger.warning(f"未知参数: {key}")