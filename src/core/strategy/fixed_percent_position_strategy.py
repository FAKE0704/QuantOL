"""
固定比例仓位管理策略

根据设计文档 docs/strategies/fixed_percent_position_strategy.md 实现
"""

import logging
from typing import Dict, Any, Optional, TYPE_CHECKING
from src.core.strategy.signal_types import SignalType

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from src.support.log.backtest_debug_logger import BacktestDebugLogger

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

    def __init__(self, percent: float = 0.1, use_initial_capital: bool = True, min_lot_size: int = 100, debug_logger: Optional['BacktestDebugLogger'] = None):
        """
        初始化固定比例仓位策略

        Args:
            percent: 仓位比例（0-1之间）
            use_initial_capital: 是否基于初始资金计算（True）或当前权益（False）
            min_lot_size: 最小交易手数
            debug_logger: 可选的调试日志记录器
        """
        if not 0 < percent <= 1:
            raise ValueError("仓位比例必须在0到1之间")

        self.percent = percent
        self.use_initial_capital = use_initial_capital
        self.min_lot_size = min_lot_size
        self.debug_logger = debug_logger  # 调试日志记录器

    def calculate_position_size(self, signal_type: SignalType, portfolio_data: Dict[str, float],
                             current_price: float, current_position: int = 0) -> int:
        """
        计算目标仓位大小

        Args:
            signal_type: 信号类型（OPEN, BUY, SELL, CLOSE, LIQUIDATE）
            portfolio_data: 投资组合数据
                - initial_capital: 初始资金
                - available_cash: 可用现金
                - total_equity: 总权益
            current_price: 当前价格
            current_position: 当前持仓数量

        Returns:
            int: 目标交易数量（正数买入，负数卖出，0表示无操作）

        Raises:
            AttributeError: 当使用的 SignalType 不存在时
            ValueError: 当参数无效时
        """

        if signal_type == SignalType.LIQUIDATE:
            return -self._calculate_liquidate_position_size(current_position)

        if signal_type == SignalType.CLOSE:
            return -self._calculate_close_position_size(current_position)

        # 计算可用资金
        available_capital = self._get_available_capital(portfolio_data)

        if signal_type == SignalType.OPEN:
            return self._calculate_open_position_size(
                portfolio_data['available_cash'], current_price, current_position
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
        raw_quantity = position_value / current_price / self.min_lot_size
        additional_quantity = int(raw_quantity) * self.min_lot_size

        # 使用调试日志记录计算过程
        self.debug_logger.log_info(
            f"_calculate_add_position_size: available_cash={available_cash:.2f}, price={current_price:.2f}, "
            f"percent={self.percent}, min_lot={self.min_lot_size}, "
            f"position_value={position_value:.2f}, raw_quantity={raw_quantity:.2f}, result={additional_quantity}"
        )

        # 检查资金是否足够
        required_cash = additional_quantity * current_price
        if required_cash > available_cash:
            additional_quantity = int(available_cash / current_price / self.min_lot_size) * self.min_lot_size
            self.debug_logger.log_info(f"_calculate_add_position_size资金不足调整后: {additional_quantity}")

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


class MartingalePositionStrategy(FixedPercentPositionStrategy):
    """
    马丁格尔仓位管理策略

    核心原则：
    - 开仓：按基础比例开仓
    - 加仓：亏损时按倍数递增仓位（multiplier^level）
    - 清仓：完全清仓所有持仓
    - 限制：最大加倍次数限制
    """

    def __init__(self, base_percent: float, multiplier: float = 2.0,
                 max_doubles: int = 5, min_lot_size: int = 100):
        """
        初始化马丁格尔仓位策略

        Args:
            base_percent: 基础仓位比例（0-1之间）
            multiplier: 加倍系数（默认2.0）
            max_doubles: 最大加倍次数（默认5）
            min_lot_size: 最小交易手数
        """
        super().__init__(percent=base_percent, min_lot_size=min_lot_size)
        self.base_percent = base_percent
        self.multiplier = multiplier
        self.max_doubles = max_doubles

        # Martingale状态（按symbol管理）
        # {symbol: {'level': int, 'entry_price': float}}
        self._martingale_states: Dict[str, Dict[str, Any]] = {}

    def _get_or_init_martingale_state(self, symbol: str) -> Dict[str, Any]:
        """获取或初始化symbol的martingale状态"""
        if symbol not in self._martingale_states:
            self._martingale_states[symbol] = {
                'level': 0,
                'entry_price': None
            }
        return self._martingale_states[symbol]

    def _reset_martingale_state(self, symbol: str):
        """重置symbol的martingale状态"""
        if symbol in self._martingale_states:
            self._martingale_states[symbol] = {
                'level': 0,
                'entry_price': None
            }
            logger.info(f"Martingale状态已重置: {symbol}")

    def calculate_position_size(self, signal_type: SignalType, portfolio_data: Dict[str, float],
                             current_price: float, current_position: int = 0, symbol: str = None) -> int:
        """
        计算目标仓位大小（Martingale版本）

        Args:
            signal_type: 信号类型（OPEN, BUY, SELL, CLOSE, LIQUIDATE）
            portfolio_data: 投资组合数据
            current_price: 当前价格
            current_position: 当前持仓数量
            symbol: 交易标的（必需，用于管理martingale状态）

        Returns:
            int: 目标交易数量（正数买入，负数卖出，0表示无操作）

        Raises:
            ValueError: 当 symbol 参数为 None 时
        """
        if symbol is None:
            raise ValueError("Martingale策略需要symbol参数")

        # 获取或初始化martingale状态
        state = self._get_or_init_martingale_state(symbol)

        # 检查持仓状态，如果清仓则重置martingale状态
        if current_position == 0 and state['level'] > 0:
            self._reset_martingale_state(symbol)
            state = self._get_or_init_martingale_state(symbol)

        # 处理清仓信号
        if signal_type == SignalType.LIQUIDATE:
            self._reset_martingale_state(symbol)
            return -self._calculate_liquidate_position_size(current_position)

        if signal_type == SignalType.CLOSE or signal_type == SignalType.SELL:
            # 完全清仓
            self._reset_martingale_state(symbol)
            return -current_position

        # 计算可用资金
        available_capital = self._get_available_capital(portfolio_data)

        # 开仓或加仓
        if signal_type in [SignalType.OPEN, SignalType.BUY]:
            if current_position == 0:
                # 开仓 - 使用基础仓位
                quantity = self._calculate_open_position_size(
                    portfolio_data['available_cash'], current_price, current_position
                )
                if quantity > 0:
                    # 记录入场价格
                    state['entry_price'] = current_price
                    state['level'] = 0
                    logger.info(f"Martingale开仓: {symbol}, 价格={current_price}, 数量={quantity}, level=0")
                return quantity
            else:
                # 加仓 - 使用martingale倍数
                return self._calculate_martingale_add_position_size(
                    symbol, portfolio_data['available_cash'], current_price, state
                )

        return 0

    def _calculate_martingale_add_position_size(self, symbol: str, available_cash: float,
                                               current_price: float, state: Dict[str, Any]) -> int:
        """
        计算Martingale加仓数量

        Args:
            symbol: 交易标的
            available_cash: 可用现金
            current_price: 当前价格
            state: martingale状态

        Returns:
            int: 加仓数量
        """
        # 检查是否达到最大加倍次数
        if state['level'] >= self.max_doubles:
            logger.warning(f"Martingale已达到最大加倍次数: {symbol}, level={state['level']}")
            return 0

        # 计算当前层级
        current_level = state['level']

        # 计算倍数（第1次加仓level=0, 倍数=1；第2次加仓level=1, 倍数=2；以此类推）
        multiplier = self.multiplier ** current_level

        # 计算基础仓位
        base_position_value = available_cash * self.base_percent
        base_quantity = int(base_position_value / current_price / self.min_lot_size) * self.min_lot_size

        # 应用martingale倍数
        martingale_quantity = int(base_quantity * multiplier / self.min_lot_size) * self.min_lot_size

        # 检查资金是否足够
        required_cash = martingale_quantity * current_price
        if required_cash > available_cash:
            # 资金不足时减少数量
            martingale_quantity = int(available_cash / current_price / self.min_lot_size) * self.min_lot_size

        # 更新martingale状态
        state['level'] += 1

        if martingale_quantity > 0:
            logger.info(
                f"Martingale加仓: {symbol}, 价格={current_price}, 数量={martingale_quantity}, "
                f"level={current_level}->{state['level']}, 倍数={multiplier:.2f}"
            )

        return martingale_quantity

    def get_strategy_info(self) -> Dict[str, Any]:
        """获取策略信息"""
        return {
            "strategy_type": "martingale",
            "base_percent": self.base_percent,
            "multiplier": self.multiplier,
            "max_doubles": self.max_doubles,
            "min_lot_size": self.min_lot_size,
            "martingale_states": self._martingale_states.copy()
        }

    def get_martingale_level(self, symbol: str) -> int:
        """获取指定symbol的当前martingale层级"""
        state = self._get_or_init_martingale_state(symbol)
        return state['level']