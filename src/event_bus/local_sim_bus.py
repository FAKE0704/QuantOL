"""本地模拟事件总线（用于回测）"""
import time
import threading
from queue import Queue, Empty
from typing import Any, Callable, Dict, List, Tuple
from . import EventBus

class LocalSimBus(EventBus):
    """基于内存的模拟事件总线"""
    
    def __init__(self, time_scale: float = 1.0):
        """
        初始化模拟总线
        :param time_scale: 时间加速因子（1.0为实时）
        """
        self.queues: Dict[str, Queue] = {}
        self.subscribers: Dict[str, List[Callable]] = {}
        self.time_scale = time_scale
        self.current_time = 0.0
        self._lock = threading.Lock()
        
    def publish(self, event_type: str, event: Any, delay: float = 0.0):
        """发布事件到指定队列"""
        with self._lock:
            if event_type not in self.queues:
                self.queues[event_type] = Queue()
            
            # 记录事件时间戳（考虑延迟和时间缩放）
            event_time = self.current_time + delay / self.time_scale
            self.queues[event_type].put((event_time, event))
            
    def subscribe(self, event_type: str, handler: Callable[[Any], None]):
        """订阅事件并启动处理线程"""
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
            threading.Thread(
                target=self._event_loop,
                args=(event_type,),
                daemon=True
            ).start()
        self.subscribers[event_type].append(handler)
        
    def _event_loop(self, event_type: str):
        """事件处理循环"""
        while True:
            try:
                event_time, event = self.queues[event_type].get_nowait()
                
                # 等待到事件时间
                while self.current_time < event_time:
                    time.sleep(0.001)  # 避免CPU占用过高
                    
                # 通知所有订阅者
                for handler in self.subscribers.get(event_type, []):
                    handler(event)
                    
            except Empty:
                time.sleep(0.01)  # 队列空时短暂等待
                
    def advance_time(self, delta: float):
        """推进模拟时间（用于回放控制）"""
        with self._lock:
            self.current_time += delta / self.time_scale
