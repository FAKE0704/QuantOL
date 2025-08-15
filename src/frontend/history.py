import streamlit as st
from datetime import datetime
import logging
from support.log.logger import logger

# 设置INFO日志级别
logger.setLevel(logging.INFO)
import logging
import pandas as pd
import plotly.graph_objects as go
import time
# import asyncio
from services.stock_search import StockSearchService
from services.chart_service import ChartService, MAIndicator, RSIIndicator, MACDIndicator
from core.data.database import DatabaseManager
from services.interaction_service import InteractionService
from ipywidgets import VBox

def update_indicator():
    """处理指标选择变化的回调函数"""
    st.session_state.current_indicator = st.session_state.indicator_select

async def show_history_page():
    st.title("历史行情")
    
    # 初始化指标选择状态
    if 'current_indicator' not in st.session_state:
        st.session_state.current_indicator = "无"
    
    # 指标选择控件
    indicator = st.selectbox(
        "选择技术指标",
        options=["无", "MA均线", "RSI", "MACD"],
        index=0,
        key='indicator_select',
        on_change=update_indicator
    )
    
    # 使用全局服务实例
    db = st.session_state.db
    search_service = st.session_state.search_service
    
    # 股票搜索（带筛选的下拉框）
    col1, col2 = st.columns([3, 1])
    with col1:
        # 初始化缓存
        if 'stock_cache' not in st.session_state or st.session_state.stock_cache is None:
            with st.spinner("正在加载股票列表..."):
                try:
                    df = await search_service.get_all_stocks()
                    st.session_state.stock_cache = list(zip(df['code'], df['code_name']))
                    st.session_state.last_stock_update = time.time()
                except Exception as e:
                    st.error(f"加载股票列表失败: {str(e)}")
                    st.session_state.stock_cache = []
        
        selected = st.selectbox(
            "搜索并选择股票",
            options=st.session_state.stock_cache,
            format_func=lambda x: f"{x[0]} {x[1]}",
            help="输入股票代码或名称进行筛选"
        )
    with col2:
        if st.button("🔄 刷新列表", help="点击手动更新股票列表"):
            st.session_state.stock_cache = None
            st.rerun()
    
    if selected:
        stock_code = selected[0]  # selected is a tuple (code, name)
        
        # 时间范围选择
        col1, col2 , col3= st.columns(3)
        with col1:
            start_date = st.date_input("开始日期")
        with col2:
            end_date = st.date_input("结束日期")
        with col3:
            frequency_options = {
                "5": "5分钟",
                "15": "15分钟",
                "30": "30分钟",
                "60": "60分钟",
                "120": "120分钟",
                "d": "日线",
                "w": "周线",
                "m": "月线",
                "y": "年线"
            }
            frequency = st.selectbox(
                "频率",
                options=list(frequency_options.keys()),
                format_func=lambda x: frequency_options[x]
            )
        
        # 日期格式转换
        start_date = pd.to_datetime(start_date).strftime('%Y-%m-%d')
        end_date = pd.to_datetime(end_date).strftime('%Y-%m-%d')

        if st.button("查看历史行情"):
            from components.progress import show_progress
            progress, status = show_progress("history_data", "正在获取数据...")
            
            # 生成包含完整信息的缓存键
            cache_key = f"history_{stock_code}_{start_date}_{end_date}_{frequency}"
            
            try:
                # 检查缓存
                # stock_cache用于股票列表，history_data_cache用于行情数据
                if 'history_data_cache' not in st.session_state:
                    st.session_state.history_data_cache = {}
                
                if cache_key not in st.session_state.history_data_cache:
                    # 获取历史数据
                    # Convert string dates to date objects
                    start_date_obj = datetime.strptime(start_date, "%Y-%m-%d").date()
                    end_date_obj = datetime.strptime(end_date, "%Y-%m-%d").date()
                    data = await db.load_stock_data(stock_code, start_date_obj, end_date_obj, frequency)
                    # 缓存数据
                    st.session_state.history_data_cache[cache_key] = data
                    logger.info(f"新获取数据: {stock_code} {start_date}至{end_date} {frequency}")
                    status.update(label="数据获取成功!", state="complete")
                else:
                    # 使用缓存数据
                    data = st.session_state.history_data_cache[cache_key]
                    logger.info(f"使用缓存数据: {stock_code} {start_date}至{end_date} {frequency}")
                    status.update(label="使用缓存数据", state="complete")
            except Exception as e:
                status.update(label=f"获取失败: {str(e)}", state="error")
                raise
            finally:
                progress.empty()

            if data is not None:
                # 显示数据表格
                st.subheader("标的信息")
                st.subheader("历史数据")
                st.dataframe(data)
                
                try:
                    # 检查必需字段
                    required_fields = ['open', 'high', 'low', 'close']
                    if not all(field in data.columns for field in required_fields):
                        raise ValueError(f"数据缺少必需字段: {required_fields}")
                        
                    # 使用ChartService绘制图表
                    from services.chart_service import DataBundle
                    data_bundle = DataBundle(raw_data=data)
                    chart_service = ChartService(data_bundle)
                    
                    # 创建三图布局 (K线图、指标图、成交量图)
                    from plotly.subplots import make_subplots
                    fig = make_subplots(
                        rows=3, cols=1,
                        shared_xaxes=True,
                        vertical_spacing=0.08,  # 增加垂直间距
                        row_heights=[0.5, 0.3, 0.2]  # 调整行高比例
                    )
                    
                    # 添加K线图
                    kline = chart_service.create_kline()
                    for trace in kline.data:
                        fig.add_trace(trace, row=1, col=1)
                    
                    # 添加指标
                    if st.session_state.current_indicator == "MA均线":
                        ma_indicator = MAIndicator([5, 10, 20])
                        for trace in ma_indicator.apply(data):
                            fig.add_trace(trace, row=1, col=1)  # MA显示在主图
                    elif st.session_state.current_indicator == "RSI":
                        rsi_indicator = RSIIndicator(window=14)
                        for trace in rsi_indicator.apply(data):
                            fig.add_trace(trace, row=2, col=1)  # RSI显示在中间
                    elif st.session_state.current_indicator == "MACD":
                        macd_indicator = MACDIndicator()
                        for trace in macd_indicator.apply(data):
                            fig.add_trace(trace, row=2, col=1)  # MACD显示在中间
                    
                    # 添加成交量图
                    volume = chart_service.create_volume_chart(auto_listen=False)
                    for trace in volume.data:
                        fig.add_trace(trace, row=3, col=1)  # 成交量显示在最下方
                    
                    # 缓存图表服务对象
                    if 'chart_service' not in st.session_state:
                        st.session_state.chart_service = chart_service
                    
                    # 更新布局
                    fig.update_layout(
                        height=1000,  # 增加总高度
                        showlegend=True,
                        hovermode="x unified",
                        margin=dict(t=30, b=30, l=30, r=30),  # 调整边距
                        xaxis=dict(rangeslider=dict(visible=False)),  # 主图
                        xaxis2=dict(rangeslider=dict(visible=False)), # 指标图
                        xaxis3=dict(rangeslider=dict(visible=False))  # 成交量图
                    )
                    
                except ValueError as e:
                    st.error(f"无法绘制图表: {str(e)}")
                    return
                except Exception as e:
                    st.error(f"绘制图表时发生错误: {str(e)}")
                    logger.error(f"图表绘制错误: {str(e)}")
                    return
                
                st.plotly_chart(fig, use_container_width=True)
            
                # # 初始化交互服务
                # interaction_service = InteractionService()
                # # 创建FigureWidget实现联动
                # fw1 = go.FigureWidget(kline)
                # fw2 = go.FigureWidget(volume)
                # # 并排显示两图
                # display(VBox([fw1, fw2]))

                # fw2.layout.on_change(kline, 'xaxis.range')
                # updated_xaxes =  await fw.update_xaxes(range=x_range)# 
                # interaction_service.subscribe(updated_xaxes)
                # # 应用共享缩放范围
                # if 'shared_xrange' in st.session_state:
                #     fw.update_xaxes(range=st.session_state.shared_xrange)

            else:
                st.error("获取数据失败，请检查股票代码和日期范围")
