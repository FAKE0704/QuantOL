import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from core.strategy.backtesting import  BacktestEngine
from core.strategy.backtesting import  BacktestConfig
from services.chart_service import  ChartService, DataBundle
from core.data.database import DatabaseManager
from core.strategy.events import ScheduleEvent, SignalEvent
from core.strategy.event_handlers import handle_schedule, handle_signal
from services.stock_search import StockSearchService
from core.strategy.strategy import FixedInvestmentStrategy
import time


async def show_backtesting_page():
    st.title("策略回测")
    
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
    
    # 时间范围选择
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("开始日期")
    with col2:
        end_date = st.date_input("结束日期")
    
    # 策略选择
    strategy = st.selectbox(
        "选择回测策略",
        options=["月定投","移动平均线交叉", "MACD交叉", "RSI超买超卖"]
    )
    
    # 策略参数设置
    # if strategy == "移动平均线交叉":
    #     short_period = st.slider("短期均线周期", min_value=5, max_value=30, value=10)
    #     long_period = st.slider("长期均线周期", min_value=20, max_value=100, value=50)
    # elif strategy == "MACD交叉":
    #     fast_period = st.slider("快速EMA周期", min_value=5, max_value=26, value=12)
    #     slow_period = st.slider("慢速EMA周期", min_value=10, max_value=50, value=26)
    #     signal_period = st.slider("信号线周期", min_value=5, max_value=20, value=9)
    # elif strategy == "RSI超买超卖":
    #     period = st.slider("RSI周期", min_value=5, max_value=30, value=14)
    #     overbought = st.slider("超买阈值", min_value=60, max_value=90, value=70)
    #     oversold = st.slider("超卖阈值", min_value=10, max_value=40, value=30)
    
    # 回测参数
    initial_capital = st.number_input("初始资金(元)", min_value=10000, value=100000)
    commission_rate = st.number_input("交易佣金(%)", min_value=0.0, max_value=1.0, value=0.03)
    
    if st.button("开始回测"):
        symbol = selected[0] # 股票代号
        frequency = "5"      # 数据频率
        start_date=start_date.strftime("%Y%m%d") # 开始日期
        end_date=end_date.strftime("%Y%m%d") # 结束日期

        
        
        # 初始化回测配置
        backtest_config = BacktestConfig(
            start_date=start_date,
            end_date=end_date,
            frequency=frequency,
            target_symbol=symbol,
            initial_capital=initial_capital,
            commission=commission_rate
        )
        
        # 初始化事件引擎
        engine = BacktestEngine(config=backtest_config)
        data = await engine.load_data(symbol)
        st.write(data) 
        # 注册事件处理器
        engine.register_handler(ScheduleEvent, handle_schedule)
        engine.register_handler(SignalEvent, handle_signal)
        
        # 初始化策略
        if strategy == "月定投":
            fixed_strategy = FixedInvestmentStrategy(
                Data=data,
                name="月定投策略",
                buySignal=True,
                sellSignal=False
            )
            engine.register_strategy(fixed_strategy)
        
        # 启动事件循环
        with st.spinner("回测进行中..."):
            engine.run(pd.to_datetime(start_date), pd.to_datetime(end_date))
        
            # 获取回测结果
            results = engine.get_results()
            equity_data = engine.equity_records
            
            if results:
                st.success("回测完成！")
                
                # 显示回测结果
                st.subheader("回测结果")
                st.dataframe(results["summary"])
                
                # 绘制净值曲线vs收盘价曲线

                st.subheader("净值曲线")
                
                # 创建净值曲线和K线图的组合图表

                databundle = DataBundle(data,equity_data)
                chart_service = ChartService(databundle)

                combined_fig = chart_service.create_combined_chart(
                    chart_types=['equity', 'kline'],
                    row_heights=[0.5, 0.5]
                )
                st.plotly_chart(combined_fig, use_container_width=True)
                
                # 显示交易记录
                st.subheader("交易记录")
                st.dataframe(results["trades"]) 
                
                # 显示仓位明细
                st.subheader("仓位明细")
                st.dataframe(equity_data)


            else:
                st.error("回测失败，请检查输入参数")
