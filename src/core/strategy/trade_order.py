"""
交易指令数据结构
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class TradeOrder:
    """交易指令"""
    symbol: str              # 交易标的代码
    quantity: int            # 交易数量（正数买入，负数卖出）
    side: str               # 交易方向（"BUY" 或 "SELL"）
    price: Optional[float] = None    # 交易价格（None表示市价单）
    timestamp: Optional[datetime] = None  # 时间戳
    strategy_id: Optional[str] = None      # 策略ID
    order_type: str = "MARKET"    # 订单类型（MARKET/LIMIT）

    def __post_init__(self):
        """数据验证和标准化"""
        # 确保side是大写的
        if self.side:
            self.side = self.side.upper()

        # 确保order_type是大写的
        if self.order_type:
            self.order_type = self.order_type.upper()

        # 设置默认时间戳
        if self.timestamp is None:
            self.timestamp = datetime.now()

    def is_buy(self) -> bool:
        """是否是买入指令"""
        return self.quantity > 0

    def is_sell(self) -> bool:
        """是否是卖出指令"""
        return self.quantity < 0

    def get_absolute_quantity(self) -> int:
        """获取绝对数量"""
        return abs(self.quantity)

    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            'symbol': self.symbol,
            'quantity': self.quantity,
            'side': self.side,
            'price': self.price,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'strategy_id': self.strategy_id,
            'order_type': self.order_type
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'TradeOrder':
        """从字典创建TradeOrder对象"""
        timestamp = data.get('timestamp')
        if timestamp and isinstance(timestamp, str):
            from datetime import datetime
            timestamp = datetime.fromisoformat(timestamp)

        return cls(
            symbol=data['symbol'],
            quantity=data['quantity'],
            side=data['side'],
            price=data.get('price'),
            timestamp=timestamp,
            strategy_id=data.get('strategy_id'),
            order_type=data.get('order_type', 'MARKET')
        )