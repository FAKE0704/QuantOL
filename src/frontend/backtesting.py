import streamlit as st
import pandas as pd
import plotly.express as px
from core.strategy.backtesting import  BacktestEngine
from core.strategy.backtesting import  BacktestConfig
from services.chart_service import  ChartService, DataBundle
from event_bus.event_types import  StrategyScheduleEvent,SignalEvent
from core.strategy.event_handlers import handle_schedule, handle_signal
from core.strategy.strategy import FixedInvestmentStrategy
from core.data.database import DatabaseManager
from services.progress_service import progress_service
from typing import cast
import time

async def show_backtesting_page():
    # 初始化策略ID
    if 'strategy_id' not in st.session_state:
        import uuid
        st.session_state.strategy_id = str(uuid.uuid4())

    st.title("策略回测")

    # 股票搜索（带筛选的下拉框）
    col1, col2 = st.columns([3, 1])
    with col1:
        # 初始化缓存
        if 'stock_cache' not in st.session_state or st.session_state.stock_cache is None:
            with st.spinner("正在加载股票列表..."):
                try:
                    stocks = await st.session_state.search_service.get_all_stocks()
                    st.session_state.stock_cache = list(zip(stocks['code'], stocks['code_name']))

                except Exception as e:
                    st.error(f"加载股票列表失败: {str(e)}")
                    st.session_state.stock_cache = []
        
        selected = st.selectbox(
            "搜索并选择股票",
            options=st.session_state.stock_cache,
            format_func=lambda x: f"{x[0]} {x[1]}",
            help="输入股票代码或名称进行筛选",
            key="stock_select",
            index = 20
        )
    with col2:
        if st.button("🔄 刷新列表", help="点击手动更新股票列表", key="refresh_button"):
            if 'stock_cache' in st.session_state:
                del st.session_state.stock_cache
            st.rerun()
    
    # 时间范围选择
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("开始日期", key="start_date_input", value= "2025-04-01")
    with col2:
        end_date = st.date_input("结束日期", key="end_date_input")
    
    # 策略选择
    strategy = st.selectbox(
        "选择回测策略",
        options=["月定投","移动平均线交叉", "MACD交叉", "RSI超买超卖", "自定义规则"],
        key="strategy_select"
    )

    # 规则编辑器
    if strategy == "自定义规则":
        with st.expander("规则编辑器", expanded=True):
            cols = st.columns([1, 2, 1])
            
            with cols[0]:
                st.subheader("指标选择")
                indicator = st.selectbox(
                    "技术指标",
                    options=["SMA", "RSI", "MACD", "VOLUME"],
                    key="indicator_select"
                )
                
                # 指标参数输入
                params = {}
                if indicator in ["SMA", "RSI"]:
                    params["n"] = st.number_input("周期", min_value=5, max_value=100, value=20 if indicator == "SMA" else 14)
                
                if st.button("添加到规则"):
                    if 'rule_expr' not in st.session_state:
                        st.session_state.rule_expr = ""
                    
                    # 构建指标调用字符串
                    param_str = ", ".join(f"{k}={v}" for k, v in params.items())
                    st.session_state.rule_expr += f"{indicator}({param_str})" if params else f"{indicator}()"
            
            with cols[1]:
                st.subheader("表达式构建")
                st.text_area("规则表达式", 
                           value=st.session_state.get("rule_expr", ""),
                           key="rule_expr_input",
                           height=100)
                
                op_cols = st.columns(7)
                with op_cols[0]: st.button(">", on_click=lambda: st.session_state.__setitem__("rule_expr", st.session_state.rule_expr + " > "))
                with op_cols[1]: st.button("<", on_click=lambda: st.session_state.__setitem__("rule_expr", st.session_state.rule_expr + " < "))
                with op_cols[2]: st.button("==", on_click=lambda: st.session_state.__setitem__("rule_expr", st.session_state.rule_expr + " == "))
                with op_cols[3]: st.button("&", on_click=lambda: st.session_state.__setitem__("rule_expr", st.session_state.rule_expr + " & "))
                with op_cols[4]: st.button("|", on_click=lambda: st.session_state.__setitem__("rule_expr", st.session_state.rule_expr + " | "))
                with op_cols[5]: st.button("(", on_click=lambda: st.session_state.__setitem__("rule_expr", st.session_state.rule_expr + " ("))
                with op_cols[6]: st.button(")", on_click=lambda: st.session_state.__setitem__("rule_expr", st.session_state.rule_expr + ") "))
                
                st.button("清空", on_click=lambda: st.session_state.__setitem__("rule_expr", ""))
            
            with cols[2]:
                st.subheader("规则预览")
                if 'rule_expr' in st.session_state and st.session_state.rule_expr:
                    try:
                        from core.strategy.rule_parser import RuleParser
                        parser = RuleParser(pd.DataFrame())  # 空DF仅用于语法检查
                        parser.parse(st.session_state.rule_expr)
                        st.success("✓ 规则语法正确")
                        st.code(st.session_state.rule_expr)
                    except Exception as e:
                        st.error(f"语法错误: {str(e)}")
                else:
                    st.info("请构建规则表达式")
    
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
    initial_capital = st.number_input("初始资金(元)", min_value=10000, value=100000, key="initial_capital_input")
    commission_rate = st.number_input("交易佣金(%)", min_value=0.0, max_value=1.0, value=0.03, key="commission_rate_input")
    
    # 初始化按钮状态
    if 'start_backtest_clicked' not in st.session_state:
        st.session_state.start_backtest_clicked = False

    # 带回调的按钮组件
    def on_backtest_click():
        st.session_state.start_backtest_clicked = not st.session_state.start_backtest_clicked

    if st.button(
        "开始回测", 
        key="start_backtest",
        on_click=on_backtest_click
    ):
        # 初始化回测配置
        symbol = selected[0] # 股票代号
        frequency = "5"      # 数据频率

        # 初始化回测参数BacktestConfig
        backtest_config = BacktestConfig( # 设置回测参数
            start_date=start_date.strftime("%Y%m%d"),  # BacktestConfig仍需要字符串格式
            end_date=end_date.strftime("%Y%m%d"),
            frequency=frequency,
            target_symbol=symbol,
            initial_capital=initial_capital,
            commission=commission_rate
        )
        
        # 初始化事件引擎BacktestEngine
        db = cast(DatabaseManager, st.session_state.db)
        data = await db.load_stock_data(symbol, start_date, end_date, frequency)  # 直接传递date对象
        engine = BacktestEngine(config=backtest_config, data=data)
        
        
        st.write("回测使用的数据") 
        st.write(data) 

        # 注册事件处理器
        engine.register_handler(StrategyScheduleEvent, handle_schedule)
        engine.register_handler(SignalEvent, handle_signal)
        
        # 初始化策略
        if strategy == "月定投":
            fixed_strategy = FixedInvestmentStrategy(
                Data=data,
                name="月定投策略",
                buySignal=True,
                sellSignal=False
            )
            # 注册策略
            engine.register_strategy(fixed_strategy)
        elif strategy == "自定义规则" and 'rule_expr' in st.session_state:
            from core.strategy.rule_based_strategy import RuleBasedStrategy
            rule_strategy = RuleBasedStrategy(
                Data=data,
                name="自定义规则策略",
                rule_expr=st.session_state.rule_expr
            )
            engine.register_strategy(rule_strategy)
        
        # 启动事件循环
        task_id = f"backtest_{st.session_state.strategy_id}"
        progress_service.start_task(task_id, 100)
        
        # 模拟进度更新  这里没有结合engine.run
        for i in range(100):
            time.sleep(0.1)  # 模拟回测过程
            progress_service.update_progress(task_id, (i + 1) / 100)
        
        engine.logger.debug("开始回测...")

        engine.run(pd.to_datetime(start_date), pd.to_datetime(end_date))
        progress_service.end_task(task_id)
        
        # 获取回测结果
        results = engine.get_results()
        data = engine.data
        equity_data = engine.equity_records

        if results:
            st.success("回测完成！")
            
            # 显示回测结果
            st.subheader("回测结果")
            st.dataframe(results["summary"])
            
            # 绘制净值曲线vs收盘价曲线

            st.subheader("净值曲线")
            
            

            # 会话级缓存ChartService实例
            @st.cache_resource(ttl=3600, show_spinner=False)
            def init_chart_service(raw_data, transaction_data):
                raw_data['open'] = raw_data['open'].astype(float)
                raw_data['high'] = raw_data['high'].astype(float)
                raw_data['low'] = raw_data['low'].astype(float)
                raw_data['close'] = raw_data['close'].astype(float)
                raw_data['combined_time'] = pd.to_datetime(raw_data['combined_time'])
                # 作图前时间排序
                raw_data = raw_data.sort_values(by = 'combined_time') 
                transaction_data = transaction_data.sort_values(by = 'timestamp')
                databundle = DataBundle(raw_data,transaction_data, capital_flow_data=None)
                return ChartService(databundle)
            
            
            if 'chart_service' not in st.session_state: # 如果缓存没有chart_service，就新建个
                st.session_state.chart_service = init_chart_service(data,equity_data)
                # debug
                # st.write(st.session_state.chart_service.data_bundle.kline_data.index)
                st.session_state.chart_instance_id = id(st.session_state.chart_service)

            chart_service = st.session_state.chart_service
            
            # 初始化回测曲线参数config_key
            config_key = f"chart_config_{st.session_state.chart_instance_id}"
            if config_key not in st.session_state:
                st.session_state[config_key] = {
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
                    }
                }

            chart_service.render_chart_controls()  # 作图配置
            # st.write(chart_service.data_bundle.kline_data)# debug
            # st.write(chart_service.data_bundle.trade_records)# debug
            chart_service.render_chart_button(st.session_state[config_key]) # 作图按钮

            
            # 显示交易记录
            st.subheader("交易记录")
            st.subheader("仓位明细")
            st.dataframe(equity_data)


        else:
            st.error("回测失败，请检查输入参数")
