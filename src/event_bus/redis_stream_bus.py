"""Redis Stream事件总线实现"""
import redis
from pickle import dumps, loads
from typing import Any, Callable
from . import EventBus

class RedisStreamBus(EventBus):
    """基于Redis Stream的有序事件总线"""
    
    def __init__(self, 
                 host: str = 'localhost', 
                 port: int = 6379,
                 consumer_group: str = 'default'):
        """
        初始化Redis连接
        :param host: Redis主机地址
        :param port: Redis端口
        :param consumer_group: 消费者组名称
        """
        self.conn = redis.Redis(host=host, port=port)
        self.group = consumer_group
        self.consumer_id = f"consumer-{id(self)}"
        
    def publish(self, event_type: str, event: Any):
        """发布事件到指定Stream"""
        try:
            # 自动生成消息ID保证时序
            self.conn.xadd(
                name=event_type,
                fields={'data': dumps(event)},
                id='*'  # 自动生成时序ID
            )
        except redis.RedisError as e:
            raise RuntimeError(f"Redis发布失败: {e}")

    def subscribe(self, 
                event_type: str, 
                handler: Callable[[Any], None]):
        """订阅Stream并处理事件"""
        try:
            # 确保消费者组存在
            self.conn.xgroup_create(
                name=event_type,
                groupname=self.group,
                id='$',
                mkstream=True
            )
        except redis.ResponseError:
            pass  # 组已存在
            
        def event_loop():
            while True:
                # 阻塞读取新消息
                messages = self.conn.xreadgroup(
                    groupname=self.group,
                    consumername=self.consumer_id,
                    streams={event_type: '>'},
                    block=0,
                    count=1
                )
                for _, msg_list in messages:
                    for msg_id, msg_data in msg_list:
                        event = loads(msg_data[b'data'])
                        handler(event)
                        # 确认消息处理完成
                        self.conn.xack(event_type, self.group, msg_id)
        
        import threading
        threading.Thread(target=event_loop, daemon=True).start()
