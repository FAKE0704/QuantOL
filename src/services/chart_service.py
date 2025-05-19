import plotly.graph_objects as go
import streamlit as st
from abc import ABC, abstractmethod
from services.theme_manager import ThemeManager
from services.interaction_service import InteractionService
import pandas as pd
import numpy as np
import plotly.express as px
from typing import List, Optional
from pandas import DataFrame
from pathlib import Path
import json
import uuid
import time
from support.log import logger


class ThemeConfig:
    def __init__(self):
        self.mode = "dark"
        self.colors = {"background": "#1E1E1E", "grid": "#404040", "text": "#FFFFFF"}
        self.font = "Arial"


class LayoutConfig:
    def __init__(self):
        self.type = "vertical"
        self.row_heights = [0.7, 0.3]
        self.spacing = 0.1
        self.grid_columns = 2


class DataConfig:
    def __init__(self):
        self.primary_fields = ["close"]
        self.secondary_fields = ["volume"]
        self.field_aliases = {"close": "收盘价", "volume": "成交量"}

    def get_display_name(self, field):
        return self.field_aliases.get(field, field)


class ChartConfig:
    """可视化配置管理"""

    def __init__(self):
        self.theme = ThemeConfig()
        self.layout = LayoutConfig()
        self.data = DataConfig()
        self._config_manager = ChartConfigManager()
        self._load_config()

    def _load_config(self):
        """加载配置文件"""
        try:
            config = self._config_manager.load_config()
            self.theme.__dict__.update(vars(config.theme))
            self.layout.__dict__.update(vars(config.layout))
            self.data.__dict__.update(vars(config.data))
        except Exception as e:
            st.error(f"配置加载失败: {str(e)}")
            self._config_manager._create_default()

    def save(self):
        """保存当前配置"""
        self._config_manager.save_config(self)


class ChartConfigManager:
    CONFIG_PATH = Path("src/support/config/chart_config.json")

    @classmethod
    def load_config(cls) -> ChartConfig:
        config = ChartConfig()
        try:
            if cls.CONFIG_PATH.exists():
                with open(cls.CONFIG_PATH, "r", encoding="utf-8") as f:
                    raw_data = json.load(f)
                    # 反序列化配置
                    config.theme.__dict__.update(raw_data.get("theme", {}))
                    config.layout.__dict__.update(raw_data.get("layout", {}))
                    config.data.__dict__.update(raw_data.get("data", {}))
        except Exception as e:
            st.error(f"配置加载失败: {str(e)}")
            return cls._create_default()
        return config

    @classmethod
    def save_config(cls, config: ChartConfig):
        """保存配置到文件"""
        try:
            cls.CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
            save_data = {
                "theme": vars(config.theme),
                "layout": vars(config.layout),
                "data": vars(config.data),
            }
            with open(cls.CONFIG_PATH, "w", encoding="utf-8") as f:
                json.dump(save_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            st.error(f"配置保存失败: {str(e)}")

    @classmethod
    def _create_default(cls) -> ChartConfig:
        """创建默认配置"""
        return ChartConfig()

    @classmethod
    def _migrate_old_config(cls, raw_data):
        """将旧版配置迁移到新结构"""
        return {
            "theme": {
                "mode": raw_data.get("current_theme", "dark"),
                "colors": raw_data.get("themes", {}),
            },
            "layout": {
                "type": raw_data.get("layout_type", "vertical"),
                "row_heights": raw_data.get("row_heights", [0.6, 0.4]),
            },
            "data": {
                "primary_fields": raw_data.get("primary_fields", []),
                "secondary_fields": raw_data.get("secondary_fields", []),
            },
        }
    @staticmethod
    def _get_default_config():

        default_config = {
            "main_chart": {
                "type": "K线图",       # 主图类型标识
                "fields": ["close"],  # 显示字段
                "data_source": "kline_data",  # 数据源标识
                "style": {            # 样式配置（参考网页4）
                    "line_width": 1.5,
                    "color": "#2c7be5"
                }
            },
            "sub_chart": {
                "show": True,         # 是否显示副图
                "type": "柱状图",      # 副图类型标识  
                "fields": ["volume"], # 显示字段
                "data_source": "trade_records", # 数据源标识
                "yaxis_name": "成交量", # Y轴标签
                "style": {
                    "type": "bar",    # 图形类型（bar/line）
                    "opacity": 0.6
                }
            },
            "version": "1.0"
        }
        return default_config
                    

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
        self.main_color = "#4E79A7"  # 主力资金颜色
        self.north_color = "#59A14F"  # 北向资金颜色

    def render(self, data: pd.DataFrame):
        from plotly.subplots import make_subplots

        # 创建双Y轴图表
        self.figure = make_subplots(specs=[[{"secondary_y": True}]])

        # 主力资金（左轴）
        self.figure.add_trace(
            go.Bar(
                x=data["date"],
                y=data["main_net"],
                name="主力净流入",
                marker_color=self.main_color,
                opacity=0.7,
            ),
            secondary_y=False,
        )

        # 北向资金（右轴）
        self.figure.add_trace(
            go.Scatter(
                x=data["date"],
                y=data["north_net"].cumsum(),
                name="北向累计",
                line=dict(color=self.north_color, width=2),
                secondary_y=True,
            )
        )

        # 应用主题配置
        theme = self.config.theme
        self.figure.update_layout(
            plot_bgcolor=theme.colors["background"],
            paper_bgcolor=theme.colors["background"],
            barmode="relative",
            title="资金流向分析",
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
        self.figure.add_trace(
            go.Candlestick(
                x=data.index,
                open=data["open"],
                high=data["high"],
                low=data["low"],
                close=data["close"],
                increasing_line_color="#25A776",
                decreasing_line_color="#EF4444",
            )
        )

        # 绘制均线
        if self.add_ma:
            for period in self.ma_periods:
                ma = data["close"].rolling(period).mean()
                self.figure.add_trace(
                    go.Scatter(x=data.index, y=ma, line=dict(width=1), opacity=0.7)
                )

        # 应用主题配置
        theme = self.config.theme
        layout = self.config.layout

        self.figure.update_layout(
            xaxis_rangeslider_visible=False,
            plot_bgcolor=theme.colors["background"],
            paper_bgcolor=theme.colors["background"],
            xaxis=dict(
                gridcolor=theme.colors["grid"],
                title_font=dict(size=12, family=theme.font),
            ),
            yaxis=dict(
                gridcolor=theme.colors["grid"],
                title_font=dict(size=12, family=theme.font),
            ),
            title_font=dict(size=14, family=theme.font),
            legend=dict(font=dict(size=10, family=theme.font)),
        )

        return self.figure


class VolumeChart(ChartBase):
    """成交量图表实现"""

    def __init__(self, config: ChartConfig):
        super().__init__(config)
        self.default_up_color = "#25A776"
        self.default_down_color = "#EF4444"

    def render(self, data: pd.DataFrame):
        # 计算涨跌颜色
        colors = np.where(
            data["close"] >= data["open"],
            self.default_up_color,
            self.default_down_color,
        )

        # 绘制成交量
        self.figure.add_trace(
            go.Bar(x=data.index, y=data["volume"], marker_color=colors, name="成交量")
        )

        # 应用主题配置
        theme = self.config.theme
        layout = self.config.layout

        self.figure.update_layout(
            title="成交量",
            plot_bgcolor=theme.colors["background"],
            paper_bgcolor=theme.colors["background"],
            xaxis=dict(
                gridcolor=theme.colors["grid"],
                title_font=dict(size=12, family=theme.font),
            ),
            yaxis=dict(
                gridcolor=theme.colors["grid"],
                title_font=dict(size=12, family=theme.font),
            ),
            title_font=dict(size=14, family=theme.font),
            legend=dict(font=dict(size=10, family=theme.font)),
        )
        return self.figure


class CombinedChartConfig(ChartConfig):
    def __init__(self):
        super().__init__()
        self.layout_type = st.sidebar.selectbox(
            "布局方式", options=["垂直堆叠", "网格排列"], index=0
        )
        self.row_heights = [0.6, 0.4]  # 默认K线+成交量高度比例
        self.vertical_spacing = 0.05


class DataBundle:
    """数据容器，用于存储多种类型的数据"""

    def __init__(
        self,
        raw_data: DataFrame = None,
        transaction_data: DataFrame = None,
        capital_flow_data: DataFrame = None,
    ):
        self.kline_data = raw_data  # K线数据
        self.trade_records = transaction_data  # 交易记录
        self.capital_flow = capital_flow_data  # 新增资金流数据字段

    def get_all_columns(self) -> list:
        """获取所有 DataFrame 的列名集合"""
        columns = set()
        # 遍历所有数据容器字段
        for attr in ["kline_data", "trade_records", "capital_flow"]:
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
        self._chart_types = {"primary": "K线图", "secondary": "K线图"}
        logger._init_logger(self)

    @st.cache_resource(show_spinner=False)
    def get_chart_service(_strategy_id: str, data_bundle: DataBundle):
        """基于策略ID的缓存实例工厂"""
        return ChartService(data_bundle)

    def _handle_config_change(*args):
        """处理配置变更的回调函数"""
        # 解析参数 - Streamlit会传递3个参数: widget_key, value, field_type
        if len(args) == 3:
            _, _, field_type = args
        else:
            field_type = args[1] if len(args) > 1 else args[0]

        # 防抖机制：如果距离上次变更时间小于300ms则忽略
        current_time = time.time()
        if current_time - st.session_state.get("last_change", 0) < 0.3:
            return
        st.session_state["last_change"] = current_time

        # 获取配置key
        config_key = f"chart_config_{st.session_state.chart_instance_id}"

        # 获取新值
        new_value = st.session_state[f"{st.session_state.strategy_id}_{field_type}"]

        # 更新配置
        if field_type in ["main_type", "main_fields"]:
            st.session_state[config_key]["main_chart"].update(
                {field_type.split("_")[1]: new_value}
            )
        elif field_type in ["sub_type", "sub_fields", "show_sub"]:
            key_map = {
                "sub_type": "type",
                "sub_fields": "fields", 
                "show_sub": "show"
            }
            st.session_state[config_key]["sub_chart"].update(
                {key_map[field_type]: new_value}
            )

        # 设置重绘标志
        st.session_state["need_redraw"] = True

    def _refresh_chart(self, config: dict):
        """根据配置刷新图表"""
        # 更新主图类型
        self._chart_types["primary"] = config["main_chart"]["type"]
        # 更新副图类型
        self._chart_types["secondary"] = config["sub_chart"]["type"]
        # 更新主图字段
        self._selected_primary_fields = config["main_chart"]["fields"]
        # 更新副图字段
        self._selected_secondary_fields = config["sub_chart"]["fields"]

    def render_chart_controls(self) -> go.Figure:
        """渲染作图配置"""
        # 生成配置key
        config_key = f"chart_config_{st.session_state.chart_instance_id}"


        # 新配置new_config初始化
        if "new_config" not in st.session_state:
            st.session_state.new_config = ChartConfigManager._get_default_config()  # 初始化默认配置
        if "config_key" not in st.session_state:
            st.session_state.config_key = ChartConfigManager._get_default_config()  # 初始化默认配置
             

        # # 片段级状态初始化
        # fragment_id = f"chart_fragment_{uuid.uuid4().hex[:8]}"
        # fragment_state = {
        #     "main_chart": {"type": "K线图", "fields": ["close"]},
        #     "sub_chart": {"show": True, "type": "柱状图", "fields": ["volume"]},
        #     "expander_expanded": True,
        #     "version": 1,
        # }




        # 渲染主图配置
        @st.fragment
        def render_main_chart_config():
            """渲染主图配置选项"""
            col1, col2 = st.columns(2)
            with col1:
                new_type = st.selectbox(
                    "主图类型",
                    options=["折线图", "K线图", "面积图"],
                    key=f"{st.session_state.strategy_id}_main_type",
                    index=["折线图", "K线图", "面积图"].index(
                        st.session_state.config_key["main_chart"]["type"]
                    ),
                    on_change=self._handle_config_change,
                    args=(config_key, "main_type"),
                )
            with col2:
                available_fields = self.data_bundle.get_all_columns()
                if new_type == "K线图":
                    required_fields = {"open", "low", "high", "close"}
                    current_fields = set(st.session_state.config_key["main_chart"]["fields"])

                    # 强制合并必选字段（不允许用户删除）
                    final_fields = list(current_fields.union(required_fields))

                    # 渲染多选框（自动选中必选字段）
                    new_fields = st.multiselect(
                        "主图字段",
                        options=available_fields,
                        default=final_fields,
                        key=f"{st.session_state.strategy_id}_main_fields",
                        on_change=self._handle_config_change,
                        args=(st.session_state.config_key, "main_fields"),
                    )

                    # 关键：强制回写必选字段，防止用户删除
                    st.session_state.config_key["main_chart"]["fields"] = list(set(new_fields).union(required_fields))
                else:
                    new_fields = st.multiselect(
                        "主图字段",
                        options=available_fields,
                        default=st.session_state.config_key["main_chart"]["fields"],
                        key=f"{st.session_state.strategy_id}_main_fields",
                        on_change=self._handle_config_change,
                        args=(st.session_state.config_key, "main_fields"),
                    )
            
            st.session_state.new_config["main_chart"]["type"] = new_type
            st.session_state.new_config["main_chart"]["fields"] = new_fields

        # 渲染副图配置
        @st.fragment
        def render_sub_chart_config():
            """渲染副图配置选项"""
            show_sub = st.checkbox(
                "显示副图",
                value=st.session_state.config_key["sub_chart"]["show"],
                key=f"{st.session_state.strategy_id}_show_sub",
                on_change=self._handle_config_change,
                args=(st.session_state.config_key, "show_sub"),
            )

            if st.session_state.config_key["sub_chart"]["show"]:
                col3, col4 = st.columns(2)
                with col3:
                    new_sub_type = st.selectbox(
                        "副图类型",
                        options=["柱状图", "折线图", "MACD"],
                        key=f"{st.session_state.strategy_id}_sub_type",
                        index=["柱状图", "折线图", "MACD"].index(
                            st.session_state.config_key["sub_chart"]["type"]
                        ),
                        on_change=self._handle_config_change,
                        args=(st.session_state.config_key, "sub_type"),
                    )
                with col4:
                    available_fields = self.data_bundle.get_all_columns()
                    new_sub_fields = st.multiselect(
                        "副图字段",
                        options=available_fields,
                        default=st.session_state.config_key["sub_chart"]["fields"],
                        key=f"{st.session_state.strategy_id}_sub_fields",
                        on_change=self._handle_config_change,
                        args=(st.session_state.config_key, "sub_fields"),
                    )
            st.session_state.new_config["sub_chart"]["type"] = new_sub_type
            st.session_state.new_config["sub_chart"]["fields"] = new_sub_fields

        # 渲染保存和重置按钮，作图
        @st.fragment
        def render_save_and_reset_buttons():
            """渲染保存和重置按钮"""
            col5, col6 = st.columns(2)
            with col5:
                if st.button("💾 保存配置", key=f"save_{config_key}"):

                    # 直接使用session_state的最新值
                    st.session_state[config_key].update(st.session_state.new_config)  # 更新保存的配置
                    self.logger.debug(f"作图配置已保存：{st.session_state.config_key}")
                    st.session_state["need_redraw"] = True

                    # 使用更轻量的通知方式
                    st.toast("✅ 配置已保存", icon="💾")
                    

            with col6:
                if st.button("🔄 重置", key=f"reset_{config_key}"):
                    st.session_state[config_key].update(ChartConfigManager._get_default_config())
                    
                    st.toast("⚡ 配置已重置", icon="🔄")
                    self.logger.debug(f"作图配置已重置：{st.session_state[config_key]}")
                    st.session_state.need_redraw = True

        # 执行渲染
        with st.expander("📊 图表配置", expanded=True):  # 确保默认展开
            render_main_chart_config()
            render_sub_chart_config()
            render_save_and_reset_buttons()

        with st.expander("会话状态监控"):
            st.write(st.session_state)


        # 版本驱动更新
        if st.session_state.get("config_version") != st.session_state.config_key["version"]:
            self._refresh_chart(st.session_state.config_key)
            st.session_state.config_version = st.session_state.config_key["version"]

        return self.figure

    @st.fragment
    def render_chart_button(self, config: dict):
        """渲染作图按钮"""

           
        
        self.logger.debug(set(config["main_chart"]["fields"]))
        
        if st.button("显示回测曲线", key="draw_backtest"):
            REQUIRED_KLINE_FIELDS = {"open", "low", "high", "close"}
            if (
                config["main_chart"]["type"] == "K线图"
                and not REQUIRED_KLINE_FIELDS.issubset(set(config["main_chart"]["fields"]))
            ):
                # 显示错误提示（支持 3 种方式）
                st.toast(":red[错误] K线图必须包含 open/low/high/close 字段", icon="🔥")  # 轻量提示
            else:
                # 确保配置已固化到会话状态
                if "config_key" not in st.session_state:
                    st.session_state.config_key = ChartConfigManager._get_default_config()  # 初始化默认配置
                
                # 生成图表
                # st.write(config)
                fig = self.create_combined_chart(config)
                st.write(fig)

    def create_interactive_chart(self) -> go.Figure:
        
        """生成交互式配置的图表"""
        # 参数有效性检查
        if not self._selected_primary_fields:
            raise ValueError("至少需要选择一个主图字段")

        # 创建基础图表
        fig = self.create_combined_chart(
            primary_cols=self._selected_primary_fields,
            secondary_cols=(
                self._selected_secondary_fields
                if self._selected_secondary_fields
                else None
            ),
        )

        # 应用图表类型样式
        if self._chart_types["primary"] == "K线图":
            fig = self._apply_candlestick_style(fig)
        elif self._chart_types["primary"] == "面积图":
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
            capital_chart.main_color = config.get("main_color", "#4E79A7")
            capital_chart.north_color = config.get("north_color", "#59A14F")

        return capital_chart.render(self.data_bundle.capital_flow)


    def create_traces(self, config, data_source, is_secondary=False):
        """动态生成trace的工厂函数"""
        trace_type_map = {
            'K线图': go.Candlestick,
            '折线图': go.Scatter,
            '柱状图': go.Bar
        }
        
        traces = []
        # graph_type = trace_type_map[config.get('type', '折线图')]
        style = config.get('style', {})
        
        count = 0
        if config.get('type', '折线图') == 'K线图':
            count = count + 1
            # self.logger.debug(f"正在作图trace_{count},graph_type = {graph_type}, fields = {config['fields']}")
            trace = self.draw_candle(data_source)
            traces.append((trace, is_secondary))
            self.logger.debug(f"my_trace is {trace}, my is_sec is {is_secondary}")
        else:
            for field in config['fields']: # 
                count = count + 1
                # self.logger.debug(f"正在作图trace_{count},graph_type = {graph_type}, fields = {config['fields']}")
                
                trace = go.Bar(
                    x=data_source.index,
                    y=data_source[field],
                    name=f"{config['type']}-{field}",
                    marker=dict(
                        opacity=style.get('opacity', 0.6),
                        color=style.get('color', '#ff7f0e')
                    )
                )
                traces.append((trace, is_secondary))
                self.logger.debug(f"my_trace is {trace}, my is_sec is {is_secondary}")
        return traces

    def draw_candle(self, data):
        return go.Candlestick(
            x=data['date'].index,
            open=data["open"],
            high=data["high"],
            low=data['low'],
            close=data['close']
        )


    def create_combined_chart(
        self,
        config: dict
    ) -> go.Figure:
        """
        创建支持单/双Y轴的组合图表

        Parameters:
        -----------
        config : dict
            图表配置字典，结构示例：
            {
                "main_chart": {
                    "type": "K线图",       # 主图类型标识
                    "fields": ["close"],  # 显示字段
                    "data_source": "kline_data",  # 数据源标识
                    "style": {            # 样式配置（参考网页4）
                        "line_width": 1.5,
                        "color": "#2c7be5"
                    }
                },
                "sub_chart": {
                    "show": True,         # 是否显示副图
                    "type": "成交量",      # 副图类型标识  
                    "fields": ["volume"], # 显示字段
                    "data_source": "trade_records", # 数据源标识
                    "yaxis_name": "成交量", # Y轴标签
                    "style": {
                        "type": "bar",    # 图形类型（bar/line）
                        "opacity": 0.6
                    }
                }
            }

        sub_chart.style.type = 'bar'  --- 柱状图            
        'scatter'  --- 折线图
        
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

        fig = make_subplots(shared_xaxes=True, specs=[[{"secondary_y": config['sub_chart'].get('show', True)}]])
        
        # st.write(self.data_bundle.kline_data.index) # debug
        # 动态处理主副图配置
        chart_configs = [
            (config['main_chart'], self.data_bundle.kline_data, False),
            (config['sub_chart'], self.data_bundle.kline_data, True)
            if config['sub_chart'].get('show') else (None, None, None)
        ]
        
        for cfg, data, secondary in chart_configs:
            if cfg and data is not None: # 有参数，有数据
                for trace, is_secondary in self.create_traces(cfg, data, secondary):
                    fig.add_trace(trace, secondary_y=is_secondary)
                    self.logger.debug(f"已添加{trace}")
        
        fig.update_layout(
            hovermode='x unified',
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            xaxis=dict(
                title="时间",
                tickvals=self.data_bundle.kline_data.index[::33],
                ticktext=self.data_bundle.kline_data["date"][::33],
                tickangle=45,
            ),
            yaxis2=dict(
                showgrid=config['sub_chart'].get('show', True),
                title=config['sub_chart'].get('yaxis_name', 'Secondary Y'),
                visible=config['sub_chart'].get('show', True)
            ) if config['sub_chart'].get('show') else {}
        )
        
        return fig

    def draw_equity(self) -> go.Figure:
        """绘制净值曲线图（包含回撤）"""
        if self.data_bundle.trade_records is None:
            raise ValueError("缺少净值数据")

        self.figure.add_trace(
            go.Scatter(
                x=self.data_bundle.trade_records["timestamp"],
                y=self.data_bundle.trade_records["total_value"],
                name="净值曲线",
                line=dict(color="#1f77b4", width=2),
            )
        )

        return self.figure

    def drawMACD(self, fast=12, slow=26, signal=9):
        """绘制MACD指标"""
        exp1 = self.data["close"].ewm(span=fast, adjust=False).mean()
        exp2 = self.data["close"].ewm(span=slow, adjust=False).mean()
        macd = exp1 - exp2
        signal_line = macd.ewm(span=signal, adjust=False).mean()
        histogram = macd - signal_line

        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=data.index,
                y=macd,
                name="MACD",
                line=dict(color="blue", width=self.default_line_width),
            )
        )
        fig.add_trace(
            go.Scatter(
                x=data.index,
                y=signal_line,
                name="Signal",
                line=dict(color="orange", width=self.default_line_width),
            )
        )
        fig.add_trace(
            go.Bar(
                x=data.index,
                y=histogram,
                name="Histogram",
                marker_color=np.where(histogram >= 0, "green", "red"),
            )
        )
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

        fig.add_trace(
            go.Scatter(
                x=data.index,
                y=data["close"],
                name="价格",
                line=dict(color="white", width=self.default_line_width),
            )
        )
        fig.add_trace(
            go.Scatter(
                x=data.index,
                y=upper_band,
                name="上轨",
                line=dict(color="red", width=self.default_line_width),
            )
        )
        fig.add_trace(
            go.Scatter(
                x=data.index,
                y=rolling_mean,
                name="中轨",
                line=dict(color="blue", width=self.default_line_width),
            )
        )
        fig.add_trace(
            go.Scatter(
                x=data.index,
                y=lower_band,
                name="下轨",
                line=dict(color="green", width=self.default_line_width),
            )
        )
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
        fig.add_trace(
            go.Bar(
                x=data.index,
                y=data["volume"],
                name="成交量",
                marker_color=colors,
            )
        )
        fig.update_layout(
            title="成交量",
            xaxis_title="时间",
            yaxis_title="成交量",
            template="plotly_dark",
        )
        st.plotly_chart(fig)

    def drawCandlestick(self):
        """绘制K线图"""
        # 初始化主题
        theme_manager = ThemeManager()
        current_theme = st.selectbox(
            "主题模式", options=list(theme_manager.themes.keys()), index=0
        )
        show_ma = st.checkbox("显示均线", value=True)
        ma_periods = st.multiselect(
            "均线周期", options=[5, 10, 20, 30, 60], default=[5, 10, 20]
        )
        # print(self.data_bundle.kline_data.dtypes)#debug
        # 初始化画布
        fig = go.Figure()
        fig.add_trace(
            go.Candlestick(
                x=self.data_bundle.kline_data['combined_time'],
                open=self.data_bundle.kline_data["open"],
                high=self.data_bundle.kline_data["high"],
                low=self.data_bundle.kline_data["low"],
                close=self.data_bundle.kline_data["close"],
                name="K线",
            )
        )
        fig = theme_manager.apply_theme(fig, current_theme)
        if show_ma and ma_periods:
            pass  # 后续补充MA作图
            # for period in ma_periods:
            #     ma = self.data_bundle.kline_data["close"].rolling(period).mean()
            #     fig.add_trace(
            #         go.Scatter(
            #             x=self.data_bundle.kline_data['combined_time'],
            #             y=ma,
            #             name=f"MA{period}",
            #             line=dict(width=1),
            #             opacity=0.7,
            #         )
            #     )
        fig.update_layout(title="K线图", xaxis_title="时间", yaxis_title="价格")
        
        return fig

    def drawRSI(self, data, window=14):
        """绘制相对强弱指数(RSI)"""
        fig = go.Figure()
        delta = data["close"].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        fig.add_trace(
            go.Scatter(
                x=data.index,
                y=rsi,
                name="RSI",
                line=dict(color="blue", width=self.default_line_width),
            )
        )
        fig.add_hline(y=30, line_dash="dash", line_color="red")
        fig.add_hline(y=70, line_dash="dash", line_color="red")
        fig.update_layout(
            title="相对强弱指数(RSI)",
            xaxis_title="时间",
            yaxis_title="RSI",
            template="plotly_dark",
        )
        st.plotly_chart(fg)

    def drawallRSI(data, window, color, line_width):
        """绘制所有RSI"""
        fig_rsi = go.Figure()
        fig_rsi.add_trace(
            go.Scatter(
                x=data.index,
                y=data[f"{window}RSI"],
                yaxis="y1",
                mode="lines",
                line=dict(color=color, width=line_width),
                name=f"{window}RSI",
                hovertext=data["time"],
                showlegend=True,
            )
        )
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
        fig4.add_trace(
            go.Scatter(
                x=data[(data["12RSI"] > 70) | (data["12RSI"] < 30)].index,
                y=data[(data["12RSI"] > 70) | (data["12RSI"] < 30)][feature1],
                yaxis="y1",
                mode="markers",
                marker=dict(color="white", size=line_width),
                name=feature1,
            )
        )
        fig4.add_trace(
            go.Scatter(
                x=data[(data["12RSI"] < 70) & (data["12RSI"] > 30)].index,
                y=data[(data["12RSI"] < 70) & (data["12RSI"] > 30)][feature1],
                yaxis="y1",
                mode="markers",
                marker=dict(color=line1_col, size=line_width),
                name=feature1,
            )
        )
        fig4.add_trace(
            go.Scatter(
                x=data[(data["12RSI"] > 70) | (data["12RSI"] < 30)].index,
                y=data[(data["12RSI"] > 70) | (data["12RSI"] < 30)]["RSI"],
                yaxis="y2",
                mode="markers",
                marker=dict(color="white", size=line_width),
                name="12RSI (Extremes)",
            )
        )
        fig4.add_trace(
            go.Scatter(
                x=data[(data["12RSI"] < 70) & (data["12RSI"] > 30)].index,
                y=data[(data["12RSI"] < 70) & (data["12RSI"] > 30)]["RSI"],
                yaxis="y2",
                mode="markers",
                marker=dict(color=line2_col, size=line_width),
                name="12RSI (Moderate)",
            )
        )
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

    def create_fund_flow_chart(self, fund_flow_data: pd.DataFrame) -> go.Figure:
        """创建资金流向图表"""
        fig = px.line(
            fund_flow_data,
            x="date",
            y=[
                "main_net_inflow_amt",
                "super_large_net_inflow_amt",
                "large_net_inflow_amt",
                "mid_net_inflow_amt",
                "retail_net_inflow_amt",
            ],
            labels={"value": "资金流向 (亿)", "date": "日期", "variable": "资金类型"},
            title="大盘资金流向分析",
        )
        fig.update_layout(
            legend_title_text="资金类型",
            xaxis_title="日期",
            yaxis_title="资金流向 (亿)",
        )
        return fig
