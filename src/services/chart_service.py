import plotly.graph_objects as go

class ChartService:
    """图表生成服务"""
    
    def __init__(self, data):
        self.data = data
        
    def create_kline(self, title="K线图") -> go.Figure:
        """生成K线图"""
        fig = go.Figure(data=[go.Candlestick(
            x=self.data.index,
            open=self.data['open'],
            high=self.data['high'],
            low=self.data['low'],
            close=self.data['close']
        )])
        fig.update_layout(title=title)
        return fig
    
    def create_volume_chart(self) -> go.Figure:
        """生成成交量图"""
        fig = go.Figure(data=[go.Bar(
            x=self.data.index,
            y=self.data['volume']
        )])
        fig.update_layout(title="成交量图")
        return fig
