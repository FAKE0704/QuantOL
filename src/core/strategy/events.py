from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict
import pandas as pd

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
class ScheduleEvent(BaseEvent):
    """定时任务事件"""
    def __init__(self, timestamp: datetime, schedule_type: str, historical_data: pd.DataFrame):
        super().__init__(timestamp, 'SCHEDULE')
        self.schedule_type = schedule_type
        self.historical_data = historical_data

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            'schedule_type': self.schedule_type,
            'historical_data': self.historical_data.to_dict(orient='records')
        })
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ScheduleEvent':
        return cls(
            timestamp=datetime.fromisoformat(data['timestamp']),
            schedule_type=data['schedule_type'],
            historical_data=pd.DataFrame(data['historical_data'])
        )

@dataclass
class SignalEvent(BaseEvent):
    """策略信号事件"""
    def __init__(self, timestamp: datetime, strategy_id: str, signal_type: str, parameters: Dict[str, Any], confidence: float):
        super().__init__(timestamp, 'SIGNAL')
        self.strategy_id = strategy_id
        self.signal_type = signal_type
        self.parameters = parameters
        self.confidence = confidence

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            'strategy_id': self.strategy_id,
            'signal_type': self.signal_type,
            'parameters': self.parameters,
            'confidence': self.confidence
        })
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SignalEvent':
      return cls(
        timestamp=datetime.fromisoformat(data['timestamp']),
        strategy_id=data['strategy_id'],
        signal_type=data['signal_type'],
        parameters=data['parameters'],
        confidence=data['confidence']
      )
