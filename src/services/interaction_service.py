from functools import wraps
import time

def debounce(wait):
    def decorator(fn):
        last_called = 0
        @wraps(fn)
        def wrapped(*args, **kwargs):
            nonlocal last_called
            now = time.time()
            if now - last_called >= wait:
                last_called = now
                return fn(*args, **kwargs)
        return wrapped
    return decorator

class InteractionService:
    """图表交互服务，负责处理图表间的联动"""
    def __init__(self):
        self.subscribers = [] # 订阅
        self.current_xrange = None #当前时间范围
        self.event_handlers = {} # 事件处理器
        self.last_xrange = None # 记录上次范围

    def subscribe(self, callback):
        """订阅图表更新事件
        Args:
            callback: 回调函数，接收x_range参数
        Returns:
            unsubscribe_func: 取消订阅的函数
        """
        self.subscribers.append(callback)
        return lambda: self.unsubscribe(callback)

    def unsubscribe(self, callback):
        """取消订阅图表更新事件"""
        if callback in self.subscribers:
            self.subscribers.remove(callback)

    MAX_RECURSION_DEPTH = 5  # 最大递归深度限制

    @debounce(0.5)  # 500ms防抖
    def handle_zoom_event(self, source: str, x_range: list):
        """处理缩放事件
        Args:
            source: 事件来源图表名称
            x_range: 新的x轴范围 [start, end]
        """
        if not hasattr(self, '_recursion_depth'):
            self._recursion_depth = 0
        
        if self._recursion_depth >= self.MAX_RECURSION_DEPTH:
            return
            
        self._recursion_depth += 1
        try:
            if x_range != self.last_xrange:  # 仅当范围变化时处理
                self.current_xrange = x_range
                self.last_xrange = x_range
                # 使用副本遍历防止回调中修改订阅列表
                for callback in self.subscribers.copy():
                    try:
                        callback(x_range)
                    except Exception as e:
                        print(f"Error in callback: {e}")
        finally:
            self._recursion_depth -= 1

    def get_current_xrange(self):
        """获取当前x轴范围"""
        return self.current_xrange

    def clear_all_listeners(self):
        """清理所有事件监听"""
        self.subscribers.clear()
        if hasattr(self, 'event_handlers'):
            self.event_handlers.clear()

    # 注册缩放回调（异步兼容）
    async def update_current_xrange(self, relayout_data) -> None:
        if 'xaxis.range[0]' in relayout_data:
            self.handle_zoom_event(
                source='kline',
                x_range=[
                    relayout_data['xaxis.range[0]'],
                    relayout_data['xaxis.range[1]']
                ]
            )
        return None

    def sync_zooming(self, figures):
        """同步多个图表的缩放
        Args:
            figures: 需要同步的图表列表
        """
        if not figures:
            return
            
        # 获取第一个图表的x轴范围
        first_fig = figures[0]
        x_range = first_fig.layout.xaxis.range
        
        # 同步所有图表的x轴范围
        for fig in figures[1:]:
            fig.update_xaxes(range=x_range)
