"""事件总线标准事件类型定义"""
from dataclasses import dataclass
from datetime import datetime
from typing import List, Dict, Any, Optional

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

@dataclass
class FillEvent:
    """成交回报事件"""
    order_id: str
    symbol: str
    fill_price: float
    fill_quantity: int
    commission: float
    timestamp: datetime

@dataclass
class SignalEvent:
    """策略信号事件"""
    strategy_id: str
    symbol: str
    signal_type: str  # ENTRY/EXIT
    strength: float  # 信号强度
    timestamp: datetime

@dataclass
class SystemEvent:
    """系统控制事件"""
    event_type: str  # START/STOP/RESET
    payload: Optional[Dict[str, Any]] = None

@dataclass
class StrategySignalEvent(BaseEvent):
    """策略信号事件"""
    strategy_id: str
    symbol: str
    direction: str  # BUY/SELL
    price: float
    quantity: int
    confidence: float
    timestamp: datetime

@dataclass
class StrategyScheduleEvent(BaseEvent):
    """策略定时任务事件"""
    schedule_type: str
    symbol: str
    parameters: Dict[str, Any]
    timestamp: datetime
