"""事件总线标准事件类型定义"""
from dataclasses import dataclass
from datetime import datetime
from typing import List, Dict, Any, Optional
from src.core.strategy.signal_types import SignalType

class BaseEvent:
    """事件基类"""
    def __init__(self, timestamp: datetime, event_type: str):
        self.timestamp = timestamp
        self.event_type = event_type

    def to_dict(self) -> Dict[str, Any]:
        """将事件转换为字典"""
        return {
            "timestamp": self.timestamp.isoformat(),
            "event_type": self.event_type
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        """从字典创建事件实例"""
        return cls(
            timestamp=datetime.fromisoformat(data['timestamp']),
            event_type=data['event_type']
        )

@dataclass
class MarketDataEvent:
    """行情数据事件"""
    symbol: str
    price: float
    volume: int
    timestamp: datetime
    exchange: str = "SH"  # 默认上交所

@dataclass
class OrderEvent:
    """订单事件"""
    strategy_id: str
    symbol: str
    direction: str  # BUY/SELL
    price: float
    quantity: int
    order_type: str = "LIMIT"  # LIMIT/MARKET
    order_id: str = ""  # 订单唯一标识符

@dataclass
class FillEvent:
    """成交回报事件"""
    order_id: str
    symbol: str
    direction: str  # BUY/SELL
    fill_price: float
    fill_quantity: int
    commission: float
    timestamp: datetime

@dataclass
class SignalEvent:
    """信号事件"""
    strategy_id: str
    symbol: str
    signal_type: str  # ENTRY/EXIT
    strength: float  # 信号强度
    timestamp: datetime
    engine: Any = None
    parameters: Dict[str, Any] = None

@dataclass
class SystemEvent:
    """系统控制事件"""
    event_type: str  # START/STOP/RESET
    payload: Optional[Dict[str, Any]] = None

@dataclass
class StrategySignalEvent(BaseEvent):
    """基于自定义规则产生的策略信号事件"""
    strategy_id: str
    symbol: str
    signal_type: SignalType  # 信号类型: OPEN/BUY/SELL/CLOSE/HEDGE/REBALANCE
    price: float
    timestamp: datetime
    quantity: int = 0  # 交易数量，0表示自动计算
    confidence: float = 1.0  # 信号置信度
    engine: Any = None
    parameters: Optional[Dict[str, Any]] = None
    position_percent: Optional[float] = None  # 用于REBALANCE信号的目标仓位比例
    hedge_ratio: Optional[float] = None  # 用于HEDGE信号的对冲比例
    
    # 向后兼容属性
    @property
    def direction(self) -> str:
        """向后兼容的direction属性"""
        if self.signal_type in [SignalType.OPEN, SignalType.BUY]:
            return "BUY"
        elif self.signal_type in [SignalType.SELL, SignalType.CLOSE]:
            return "SELL"
        else:
            return ""
    
    @direction.setter
    def direction(self, value: str):
        """设置direction时自动转换signal_type"""
        if value == "BUY":
            self.signal_type = SignalType.BUY
        elif value == "SELL":
            self.signal_type = SignalType.SELL

@dataclass
class StrategyScheduleEvent(BaseEvent):
    """策略定时任务事件"""
    schedule_type: str  # 
    symbol: str
    timestamp: datetime
    current_index: int  # 新增：当前数据索引位置
    engine: Any = None  # 添加engine字段保持兼容性
    parameters: Optional[Dict[str, Any]] = None

@dataclass
class TradingDayEvent(BaseEvent):
    """交易日事件"""
    timestamp: datetime
    is_first_day: bool = False

@dataclass
class PortfolioPositionUpdateEvent(BaseEvent):
    """投资组合持仓更新事件"""
    timestamp: datetime
    symbol: str
    quantity: float
    avg_cost: float
    current_value: float
    cash_balance: float
    portfolio_value: float
    update_type: str = "SINGLE"  # SINGLE/BATCH
    success: bool = True
    error_message: Optional[str] = None
