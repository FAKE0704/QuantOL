class InteractionService:
    """图表交互服务，负责处理图表间的联动"""
    def __init__(self):
        self.subscribers = [] # 订阅
        self.current_xrange = None #当前时间范围

    def subscribe(self, callback):
        """订阅图表更新事件
        Args:
            callback: 回调函数，接收x_range参数
        """
        self.subscribers.append(callback)

    def handle_zoom_event(self, source: str, x_range: list):
        """处理缩放事件
        Args:
            source: 事件来源图表名称
            x_range: 新的x轴范围 [start, end]
        """
        self.current_xrange = x_range
        for callback in self.subscribers:
            try:
                callback(x_range)
            except Exception as e:
                print(f"Error in callback: {e}")

    def get_current_xrange(self):
        """获取当前x轴范围"""
        return self.current_xrange

    # 注册缩放回调（异步兼容）
    async def update_current_xrange(self,relayout_data)->None:
      if 'xaxis.range[0]' in relayout_data:
        await self.handle_zoom_event(
          source='kline',
          x_range=[
            relayout_data['xaxis.range[0]'],
            relayout_data['xaxis.range[1]']
          ]
        )



        