"""事件总线核心模块"""
from abc import ABC, abstractmethod
from typing import Callable, Any

class EventBus(ABC):
    """事件总线抽象基类"""
    @abstractmethod
    def publish(self, event_type: str, event: object):
        """发布事件"""
        pass

    @abstractmethod
    def subscribe(self, event_type: str, handler: Callable[[Any], Any]):
        """订阅事件"""
        pass
