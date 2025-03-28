import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import time
import asyncio
from services.stock_search import StockSearchService
from services.chart_service import ChartService
from core.data.database import DatabaseManager
from services.interaction_service import InteractionService
from ipywidgets import VBox

async def show_history_page():
    st.title("历史行情")
    
    # 初始化服务
    search_service = StockSearchService()
    await search_service.async_init()
    db = DatabaseManager()
    
    # 股票搜索（带筛选的下拉框）
    col1, col2 = st.columns([3, 1])
    with col1:
        # 初始化缓存
        if 'stock_cache' not in st.session_state or st.session_state.stock_cache is None:
            with st.spinner("正在加载股票列表..."):
                try:
                    st.session_state.stock_cache = await search_service.get_all_stocks()
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
            frequency = st.selectbox("频率", ["5","15","30","60","120","d","w","m","y"])
        
        if st.button("查看历史行情"):
            from components.progress import show_progress
            progress, status = show_progress("history_data", "正在获取数据...")
            
            try:
                # 获取历史数据
                data = await db.load_stock_data(stock_code, start_date, end_date, frequency)
                status.update(label="数据获取成功!", state="complete")
            except Exception as e:
                status.update(label=f"获取失败: {str(e)}", state="error")
                raise
            finally:
                progress.empty()

            if data is not None:
                # 显示数据表格
                st.subheader("历史数据")
                st.dataframe(data)
                
                

                # 使用ChartService绘制图表
                chart_service = ChartService(data)
                
                # K线图
                st.subheader("K线图")
                kline = chart_service.create_kline()
                st.plotly_chart(kline, use_container_width=True)
                
                # 成交量图
                st.subheader("成交量图")
                volume = chart_service.create_volume_chart()
                st.plotly_chart(volume, use_container_width=True)
            
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
