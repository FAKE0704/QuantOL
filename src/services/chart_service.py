import plotly.graph_objects as go
import streamlit as st
from abc import ABC, abstractmethod
from services.theme_manager import ThemeManager
from services.interaction_service import InteractionService
import pandas as pd
import numpy as np
from typing import List, Optional
from pandas import DataFrame
from pathlib import Path
import json

class ChartConfigManager:
    CONFIG_PATH = Path("src/support/config/chart_config.json")
    
    @classmethod
    def load_config(cls) -> dict:
        """加载持久化配置"""
        try:
            if cls.CONFIG_PATH.exists():
                with open(cls.CONFIG_PATH, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            st.error(f"配置加载失败: {str(e)}")
        return cls._get_default_config()

    @classmethod
    def save_config(cls, config: dict):
        """保存配置到文件"""
        try:
            cls.CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
            with open(cls.CONFIG_PATH, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            st.error(f"配置保存失败: {str(e)}")

    @staticmethod
    def _get_default_config() -> dict:
        """获取默认配置"""
        return {
            "primary_type": "折线图",
            "primary_fields": ["close"],
            "show_secondary": True,
            "secondary_type": "柱状图", 
            "secondary_fields": ["volume"]
        }

class ChartConfig:
    """可视化配置管理"""
    def __init__(self):
        # 初始化主题管理器
        theme_manager = ThemeManager()
        # 主题选择
        self.current_theme = st.sidebar.selectbox(
            "主题模式",
            options=list(theme_manager.themes.keys()),
            index=0,
            key=f"theme_select_{id(self)}"
        )
        self.themes = {
            'dark': {'bg_color': '#1E1E1E', 'grid_color': '#404040'},
            'light': {'bg_color': '#FFFFFF', 'grid_color': '#E0E0E0'}
        }

class ChartBase(ABC):
    """图表基类"""
    def __init__(self, config: ChartConfig):
        self.config = config
        self.figure = go.Figure()

    @abstractmethod
    def render(self, data: pd.DataFrame):
        pass

class CapitalFlowChart(ChartBase):
    """资金流图表实现"""
    def __init__(self, config: ChartConfig):
        super().__init__(config)
        self.main_color = '#4E79A7'  # 主力资金颜色
        self.north_color = '#59A14F'  # 北向资金颜色
        
    def render(self, data: pd.DataFrame):
        from plotly.subplots import make_subplots
        # 创建双Y轴图表
        self.figure = make_subplots(specs=[[{"secondary_y": True}]])
        
        # 主力资金（左轴）
        self.figure.add_trace(go.Bar(
            x=data['date'],
            y=data['main_net'],
            name='主力净流入',
            marker_color=self.main_color,
            opacity=0.7
        ), secondary_y=False)
        
        # 北向资金（右轴） 
        self.figure.add_trace(go.Scatter(
            x=data['date'],
            y=data['north_net'].cumsum(),
            name='北向累计',
            line=dict(color=self.north_color, width=2),
            secondary_y=True
        ))
        
        # 应用主题配置
        theme = self.config.themes[self.config.current_theme]
        self.figure.update_layout(
            plot_bgcolor=theme['bg_color'],
            paper_bgcolor=theme['bg_color'],
            barmode='relative',
            title='资金流向分析'
        )
        return self.figure

class CandlestickChart(ChartBase):
    """K线图表实现"""
    def __init__(self, config: ChartConfig):
        super().__init__(config)
        self.add_ma = True
        self.ma_periods = [5, 10, 20]

    def render(self, data: pd.DataFrame):
        """K线图表渲染"""

        # 绘制K线
        self.figure.add_trace(go.Candlestick(
            x=data.index,
            open=data['open'],
            high=data['high'],
            low=data['low'],
            close=data['close'],
            increasing_line_color='#25A776',
            decreasing_line_color='#EF4444'
        ))
        
        # 绘制均线
        if self.add_ma:
            for period in self.ma_periods:
                ma = data['close'].rolling(period).mean()
                self.figure.add_trace(go.Scatter(
                    x=data.index,
                    y=ma,
                    line=dict(width=1),
                    opacity=0.7
                ))

        # 应用主题
        theme = self.config.themes[self.config.current_theme]

        self.figure.update_layout(
            xaxis_rangeslider_visible=False,
            plot_bgcolor=theme['bg_color'],
            paper_bgcolor=theme['bg_color'],
            xaxis=dict(gridcolor=theme['grid_color']),
            yaxis=dict(gridcolor=theme['grid_color'])
        )
        
        return self.figure

class VolumeChart(ChartBase):
    """成交量图表实现"""
    def __init__(self, config: ChartConfig):
        super().__init__(config)
        self.default_up_color = '#25A776'
        self.default_down_color = '#EF4444'

    def render(self, data: pd.DataFrame):
        # 计算涨跌颜色
        colors = np.where(data['close'] >= data['open'], 
                        self.default_up_color, 
                        self.default_down_color)
        
        # 绘制成交量
        self.figure.add_trace(go.Bar(
            x=data.index,
            y=data['volume'],
            marker_color=colors,
            name='成交量'
        ))

        # 应用主题
        theme = self.config.themes[self.config.current_theme]
        self.figure.update_layout(
            title='成交量',
            plot_bgcolor=theme['bg_color'],
            paper_bgcolor=theme['bg_color'],
            xaxis=dict(gridcolor=theme['grid_color']),
            yaxis=dict(gridcolor=theme['grid_color'])
        )
        return self.figure

class CombinedChartConfig(ChartConfig):
    def __init__(self):
        super().__init__()
        self.layout_type = st.sidebar.selectbox(
            "布局方式",
            options=["垂直堆叠", "网格排列"],
            index=0
        )
        self.row_heights = [0.6, 0.4]  # 默认K线+成交量高度比例
        self.vertical_spacing = 0.05

class DataBundle:
    """数据容器，用于存储多种类型的数据"""
    def __init__(self, raw_data : DataFrame = None, transaction_data : DataFrame =None, capital_flow_data : DataFrame =None):
        self.kline_data = raw_data  # K线数据
        self.trade_records = transaction_data  # 交易记录
        self.capital_flow = capital_flow_data  # 新增资金流数据字段

    def get_all_columns(self) -> list:
        """获取所有 DataFrame 的列名集合"""
        columns = set()
        # 遍历所有数据容器字段
        for attr in ['kline_data', 'trade_records', 'capital_flow']:
            df = getattr(self, attr)
            if df is not None and isinstance(df, DataFrame):
                columns.update(df.columns.tolist())
        return columns

class ChartService:
    """图表服务，支持多种数据源的图表绘制"""
    def __init__(self, data_bundle: DataBundle):
        self.data_bundle = data_bundle
        self.interaction_service = InteractionService()
        self.figure = go.Figure()
        self._selected_primary_fields = [] 
        self._selected_secondary_fields = []
        self._chart_types = {
            'primary': 'K线图',
            'secondary': 'K线图'
        }
    
    def render_chart_controls(self) -> go.Figure:
        """渲染图表配置控件（带状态管理）"""
        # 清理旧的事件监听
        if hasattr(self, 'interaction_service'):
            self.interaction_service.clear_all_listeners()

        # 初始化session_state配置
        config_key = f"chart_config_{id(self)}"
        if config_key not in st.session_state:
            st.session_state[config_key] = {
                'version': 1,
                'main_chart': {
                    'type': 'K线图',
                    'fields': ['close'],
                    'components': {}
                },
                'sub_chart': {
                    'show': True,
                    'type': '柱状图',
                    'fields': ['volume'],
                    'components': {}
                },
            }

        config = st.session_state[config_key]

        # 使用独立的key来管理每个控件
        with st.expander("📊 图表配置", expanded=True):
            # 主图配置
            col1, col2 = st.columns(2)
            with col1:
                new_type = st.selectbox(
                    "主图类型",
                    options=["折线图", "K线图", "面积图"],
                    key=f"{id(self)}v{config['version']}_main_type",
                    index=["折线图", "K线图", "面积图"].index(config['main_chart']['type'])
                )
                if new_type != config['main_chart']['type']:
                    config['main_chart']['type'] = new_type
                    config['version'] += 1

            with col2:
                available_fields = self.data_bundle.get_all_columns()
                new_fields = st.multiselect(
                    "主图字段",
                    options=available_fields,
                    default=config['main_chart']['fields'],
                    key=f"{id(self)}v{config['version']}_main_fields"
                )
                if set(new_fields) != set(config['main_chart']['fields']):
                    config['main_chart']['fields'] = new_fields
                    config['version'] += 1

            # 副图配置
            show_sub = st.checkbox(
                "显示副图",
                value=config['sub_chart']['show'],
                key=f"{id(self)}v{config['version']}_show_sub"
            )
            if show_sub != config['sub_chart']['show']:
                config['sub_chart']['show'] = show_sub
                config['version'] += 1

            if config['sub_chart']['show']:
                col3, col4 = st.columns(2)
                with col3:
                    new_sub_type = st.selectbox(
                        "副图类型",
                        options=["柱状图", "折线图", "MACD"],
                        key=f"{id(self)}v{config['version']}_sub_type",
                        index=["柱状图", "折线图", "MACD"].index(config['sub_chart']['type'])
                    )
                    if new_sub_type != config['sub_chart']['type']:
                        config['sub_chart']['type'] = new_sub_type
                        config['version'] += 1

                with col4:
                    new_sub_fields = st.multiselect(
                        "副图字段",
                        options=available_fields,
                        default=config['sub_chart']['fields'],
                        key=f"{id(self)}v{config['version']}_sub_fields"
                    )
                    if set(new_sub_fields) != set(config['sub_chart']['fields']):
                        config['sub_chart']['fields'] = new_sub_fields
                        config['version'] += 1

            # 配置管理
            col5, col6 = st.columns(2)
            with col5:
                if st.button("💾 保存配置", key=f"save_{config_key}"):
                    ChartConfigManager.save_config({
                        'primary_type': config['main_chart']['type'],
                        'primary_fields': config['main_chart']['fields'],
                        'show_secondary': config['sub_chart']['show'],
                        'secondary_type': config['sub_chart']['type'],
                        'secondary_fields': config['sub_chart']['fields']
                    })
                    st.success("配置已保存!")
            with col6:
                if st.button("🔄 重置", key=f"reset_{config_key}"):
                    default_config = ChartConfigManager._get_default_config()
                    config.update({
                        'main_chart': {
                            'type': default_config['primary_type'],
                            'fields': default_config['primary_fields']
                        },
                        'sub_chart': {
                            'show': default_config['show_secondary'],
                            'type': default_config['secondary_type'],
                            'fields': default_config['secondary_fields']
                        },
                        'version': config['version'] + 1
                    })
                    st.experimental_rerun()

        # 直接比对配置变更
        prev_main = config['main_chart'].copy()
        prev_sub = config['sub_chart'].copy()
        
        if (config['main_chart'] != prev_main 
           or config['sub_chart'] != prev_sub):
            config['version'] += 1
            # 同步到实例变量
            self._chart_types = {
                'primary': config['main_chart']['type'],
                'secondary': config['sub_chart']['type']
            }
            self._selected_primary_fields = config['main_chart']['fields']
            self._selected_secondary_fields = config['sub_chart']['fields']
        
        return self.figure

    def create_interactive_chart(self) -> go.Figure:
        """生成交互式配置的图表"""
        # 参数有效性检查
        if not self._selected_primary_fields:
            raise ValueError("至少需要选择一个主图字段")

        # 创建基础图表
        fig = self.create_combined_chart(
            primary_cols=self._selected_primary_fields,
            secondary_cols=self._selected_secondary_fields if self._selected_secondary_fields else None
        )

        # 应用图表类型样式
        if self._chart_types['primary'] == 'K线图':
            fig = self._apply_candlestick_style(fig)
        elif self._chart_types['primary'] == '面积图':
            fig = self._apply_area_style(fig, self._selected_primary_fields)

        return fig

    def create_kline(self) -> go.Figure:
        """创建K线图"""
        if self.data_bundle.kline_data is None:
            raise ValueError("缺少K线数据")

        # 配置作图参数
        config = ChartConfig()
        kline = CandlestickChart(config)
        fig = kline.render(self.data_bundle.kline_data)
        self.figure = fig
        return fig

    def create_volume_chart(self) -> go.Figure:
        """创建成交量图"""
        if self.data_bundle.kline_data is None:
            raise ValueError("缺少K线数据")
            
        config = ChartConfig()
        volume = VolumeChart(config)
        fig = volume.render(self.data_bundle.kline_data)
        return fig

    def create_capital_flow_chart(self, config: dict = None) -> go.Figure:
        """创建资金流图表"""
        if self.data_bundle.capital_flow is None:
            raise ValueError("缺少资金流数据")
            
        # 初始化配置
        flow_config = ChartConfig()
        capital_chart = CapitalFlowChart(flow_config)
        
        # 应用自定义配置
        if config:
            capital_chart.main_color = config.get('main_color', '#4E79A7')
            capital_chart.north_color = config.get('north_color', '#59A14F')
            
        return capital_chart.render(self.data_bundle.capital_flow)

    def create_combined_chart(
        self,
        primary_cols: List[str],
        secondary_cols: Optional[List[str]] = None,
        secondary_y_name: str = "Secondary Y"
    ) -> go.Figure:
        """
        创建支持单/双Y轴的组合图表

        Parameters:
        -----------
        databundle:DataBundle
            包含图表数据的DataFrame，索引应为时间序列
        primary_cols : List[str]
            主Y轴要显示的数据列名称列表
        secondary_cols : Optional[List[str]], default=None
            次Y轴要显示的数据列名称列表，为None时不显示次Y轴
        secondary_y_name : str, default="Secondary Y"
            次Y轴的名称标签

        Returns:
        --------
        go.Figure
            配置好的Plotly图表对象

        Examples:
        ---------
        >>> # 单Y轴调用
        >>> fig = create_combined_chart(df, ['close', 'MA20'])
        
        >>> # 双Y轴调用
        >>> fig = create_combined_chart(df, ['close'], ['volume'], "成交量")
        """
        from plotly.subplots import make_subplots
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        
        # 主Y轴绘图
        for col in primary_cols:
            fig.add_trace(
                go.Scatter(x=self.data_bundle.kline_data['combined_time'], y=self.data_bundle.kline_data[col], name=col),
                secondary_y=False
            )

        # 次Y轴绘图
        if secondary_cols:
            for col in secondary_cols:
                fig.add_trace(
                    go.Scatter(
                        x=self.data_bundle.trade_records.timestamp, 
                        y=self.data_bundle.trade_records[col], 
                        name=f"{col} ({secondary_y_name})"
                    ),
                secondary_y=True
            )
            fig.update_layout(yaxis2=dict(title=secondary_y_name))
        self.figure = fig
        return fig

    def draw_equity(self) -> go.Figure:
        """绘制净值曲线图（包含回撤）"""
        if self.data_bundle.trade_records is None:
            raise ValueError("缺少净值数据")
            
        self.figure.add_trace(go.Scatter(
            x=self.data_bundle.trade_records['timestamp'],
            y=self.data_bundle.trade_records['total_value'],
            name='净值曲线',
            line=dict(color='#1f77b4', width=2)
        ))
        
        return self.figure

    def drawMACD(self, fast=12, slow=26, signal=9):
        """绘制MACD指标"""
        exp1 = self.data["close"].ewm(span=fast, adjust=False).mean()
        exp2 = self.data["close"].ewm(span=slow, adjust=False).mean()
        macd = exp1 - exp2
        signal_line = macd.ewm(span=signal, adjust=False).mean()
        histogram = macd - signal_line

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=data.index,
            y=macd,
            name="MACD",
            line=dict(color="blue", width=self.default_line_width),
        ))
        fig.add_trace(go.Scatter(
            x=data.index,
            y=signal_line,
            name="Signal",
            line=dict(color="orange", width=self.default_line_width),
        ))
        fig.add_trace(go.Bar(
            x=data.index,
            y=histogram,
            name="Histogram",
            marker_color=np.where(histogram >= 0, "green", "red"),
        ))
        fig.update_layout(
            title="MACD", xaxis_title="时间", yaxis_title="MACD", template="plotly_dark"
        )
        st.plotly_chart(fig)

    def drawBollingerBands(self, data, window=20, num_std=2):
        """绘制布林带"""
        fig = go.Figure()
        rolling_mean = data["close"].rolling(window=window).mean()
        rolling_std = data["close"].rolling(window=window).std()
        upper_band = rolling_mean + (rolling_std * num_std)
        lower_band = rolling_mean - (rolling_std * num_std)

        fig.add_trace(go.Scatter(
            x=data.index,
            y=data["close"],
            name="价格",
            line=dict(color="white", width=self.default_line_width),
        ))
        fig.add_trace(go.Scatter(
            x=data.index,
            y=upper_band,
            name="上轨",
            line=dict(color="red", width=self.default_line_width),
        ))
        fig.add_trace(go.Scatter(
            x=data.index,
            y=rolling_mean,
            name="中轨",
            line=dict(color="blue", width=self.default_line_width),
        ))
        fig.add_trace(go.Scatter(
            x=data.index,
            y=lower_band,
            name="下轨",
            line=dict(color="green", width=self.default_line_width),
        ))
        fig.update_layout(
            title="布林带",
            xaxis_title="时间",
            yaxis_title="价格",
            template="plotly_dark",
        )
        st.plotly_chart(fig)

    def drawVolume(self, data):
        """绘制成交量图"""
        fig = go.Figure()
        colors = np.where(data["close"] >= data["open"], "green", "red")
        fig.add_trace(go.Bar(
            x=data.index,
            y=data["volume"],
            name="成交量",
            marker_color=colors,
        ))
        fig.update_layout(
            title="成交量",
            xaxis_title="时间",
            yaxis_title="成交量",
            template="plotly_dark",
        )
        st.plotly_chart(fig)

    def drawCandlestick(self, data):
        """绘制K线图"""
        theme_manager = ThemeManager()
        current_theme = st.sidebar.selectbox(
            "主题模式",
            options=list(theme_manager.themes.keys()),
            index=0
        )
        show_ma = st.sidebar.checkbox("显示均线", value=True)
        ma_periods = st.sidebar.multiselect(
            "均线周期",
            options=[5, 10, 20, 30, 60],
            default=[5, 10, 20]
        )
        fig = go.Figure()
        fig.add_trace(go.Candlestick(
            x=self.data.index,
            open=self.data['open'],
            high=self.data['high'],
            low=self.data['low'],
            close=self.data['close'],
            name='K线'
        ))
        fig = theme_manager.apply_theme(fig, current_theme)
        if show_ma and ma_periods:
            for period in ma_periods:
                ma = data['close'].rolling(period).mean()
                fig.add_trace(go.Scatter(
                    x=data.index,
                    y=ma,
                    name=f'MA{period}',
                    line=dict(width=1),
                    opacity=0.7
                ))
        fig.update_layout(
            title="K线图",
            xaxis_title="时间",
            yaxis_title="价格"
        )
        fw = go.FigureWidget(fig)
        interaction_service = InteractionService()
        def update_kline_xrange(relayout_data):
            if 'xaxis.range[0]' in relayout_data:
                interaction_service.handle_zoom_event(
                    source='kline',
                    x_range=[
                        relayout_data['xaxis.range[0]'],
                        relayout_data['xaxis.range[1]']
                    ]
                )
        fw.layout.on_change(update_kline_xrange, 'xaxis.range')
        def update_other_charts(x_range):
            fw.update_xaxes(range=x_range)
        interaction_service.subscribe(update_other_charts)
        if 'shared_xrange' in st.session_state:
            fw.update_xaxes(range=st.session_state.shared_xrange)
        st.plotly_chart(fw, use_container_width=True)

    def drawRSI(self, data, window=14):
        """绘制相对强弱指数(RSI)"""
        fig = go.Figure()
        delta = data["close"].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        fig.add_trace(go.Scatter(
            x=data.index,
            y=rsi,
            name="RSI",
            line=dict(color="blue", width=self.default_line_width),
        ))
        fig.add_hline(y=30, line_dash="dash", line_color="red")
        fig.add_hline(y=70, line_dash="dash", line_color="red")
        fig.update_layout(
            title="相对强弱指数(RSI)",
            xaxis_title="时间",
            yaxis_title="RSI",
            template="plotly_dark",
        )
        st.plotly_chart(fig)

    def drawallRSI(data, window, color, line_width):
        """绘制所有RSI"""
        fig_rsi = go.Figure()
        fig_rsi.add_trace(go.Scatter(
            x=data.index,
            y=data[f"{window}RSI"],
            yaxis="y1",
            mode="lines",
            line=dict(color=color, width=line_width),
            name=f"{window}RSI",
            hovertext=data["time"],
            showlegend=True,
        ))
        fig_rsi.add_hline(
            y=30,
            line_dash="dash",
            line_color="white",
            annotation_text="y=30",
            annotation_position="top left",
        )
        fig_rsi.add_hline(
            y=70,
            line_dash="dash",
            line_color="white",
            annotation_text="y=70",
            annotation_position="top left",
        )
        fig_rsi.update_layout(
            title=f"{window}RSI",
            xaxis=dict(
                gridcolor="white",
                title="时间",
                tickvals=data.index[::1000],
                ticktext=data["time"][::1000],
            ),
            yaxis=dict(
                gridcolor="white",
                title=f"{window}RSI",
                titlefont=dict(color="white"),
                tickfont=dict(color="white"),
                tickvals=[30, 70],
                ticktext=["30", "70"],
            ),
            template="plotly",
            legend=dict(x=0.1, y=1.1),
            hovermode="x unified",
        )
        st.plotly_chart(fig_rsi)

    def drawRSI(data, feature1, line1_col, RSI, line2_col, line_width):
        """绘制RSI相关图表"""
        fig4 = go.Figure()
        fig4.add_trace(go.Scatter(
            x=data[(data["12RSI"] > 70) | (data["12RSI"] < 30)].index,
            y=data[(data["12RSI"] > 70) | (data["12RSI"] < 30)][feature1],
            yaxis="y1",
            mode="markers",
            marker=dict(color="white", size=line_width),
            name=feature1,
        ))
        fig4.add_trace(go.Scatter(
            x=data[(data["12RSI"] < 70) & (data["12RSI"] > 30)].index,
            y=data[(data["12RSI"] < 70) & (data["12RSI"] > 30)][feature1],
            yaxis="y1",
            mode="markers",
            marker=dict(color=line1_col, size=line_width),
            name=feature1,
        ))
        fig4.add_trace(go.Scatter(
            x=data[(data["12RSI"] > 70) | (data["12RSI"] < 30)].index,
            y=data[(data["12RSI"] > 70) | (data["12RSI"] < 30)]["RSI"],
            yaxis="y2",
            mode="markers",
            marker=dict(color="white", size=line_width),
            name="12RSI (Extremes)",
        ))
        fig4.add_trace(go.Scatter(
            x=data[(data["12RSI"] < 70) & (data["12RSI"] > 30)].index,
            y=data[(data["12RSI"] < 70) & (data["12RSI"] > 30)]["RSI"],
            yaxis="y2",
            mode="markers",
            marker=dict(color=line2_col, size=line_width),
            name="12RSI (Moderate)",
        ))
        fig4.update_layout(
            title="xxx",
            xaxis=dict(
                title="时间",
                tickvals=data.index[::1000],
                ticktext=data["time"][::1000],
                tickangle=45,
            ),
            yaxis=dict(
                title=f"feature1",
                titlefont=dict(color="blue"),
                tickfont=dict(color="blue"),
            ),
            yaxis2=dict(
                title=f"RSI",
                titlefont=dict(color="orange"),
                tickfont=dict(color="orange"),
                overlaying="y",
                side="right",
            ),
            template="plotly",
            legend=dict(x=0.5, y=1.1),
            hovermode="x unified",
        )
        st.title("股票图像")
        st.plotly_chart(fig4)
