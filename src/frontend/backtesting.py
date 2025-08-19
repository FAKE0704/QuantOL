import streamlit as st
import pandas as pd
import plotly.express as px
from core.strategy.backtesting import  BacktestEngine
from core.strategy.backtesting import  BacktestConfig
from services.chart_service import  ChartService, DataBundle
from event_bus.event_types import StrategyScheduleEvent, StrategySignalEvent
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
    
    col1, col2 = st.columns(2)
    with col1:
        # 策略选择
        strategy = st.selectbox(
            "选择回测策略",
            options=["月定投","移动平均线交叉", "MACD交叉", "RSI超买超卖", "自定义规则"],
            key="strategy_select"
        )
    with col2:
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
    
    

    # 规则编辑器
    if strategy == "自定义规则":
        with st.expander("规则编辑器", expanded=True):
            cols = st.columns([3, 1])
            
            with cols[0]:
                st.subheader("买入规则")
                st.text_area(
                    "买入条件", 
                    value=st.session_state.get("buy_rule_expr", ""),
                    height=100,
                    key="buy_rule_input",
                    help="输入买入条件表达式，如: SMA(20) > SMA(50)"
                )
                
                st.subheader("卖出规则") 
                st.text_area(
                    "卖出条件",
                    value=st.session_state.get("sell_rule_expr", ""),
                    height=100,
                    key="sell_rule_input",
                    help="输入卖出条件表达式，如: SMA(20) < SMA(50)"
                )
            
            with cols[1]:
                st.subheader("规则语法校验")
                if 'buy_rule_expr' in st.session_state and st.session_state.buy_rule_expr:
                    from core.strategy.rule_parser import RuleParser
                    valid, msg = RuleParser.validate_syntax(st.session_state.buy_rule_expr)
                    if valid:
                        st.success("✓ 买入规则语法正确")
                        st.code(f"买入: {st.session_state.buy_rule_expr}")
                    else:
                        st.error(msg)
                
                if 'sell_rule_expr' in st.session_state and st.session_state.sell_rule_expr:
                    from core.strategy.rule_parser import RuleParser
                    valid, msg = RuleParser.validate_syntax(st.session_state.sell_rule_expr)
                    if valid:
                        st.success("✓ 卖出规则语法正确")
                        st.code(f"卖出: {st.session_state.sell_rule_expr}")
                    else:
                        st.error(msg)
                
                if not st.session_state.get('buy_rule_expr') and not st.session_state.get('sell_rule_expr'):
                    st.info("请输入买入/卖出规则表达式")
                
                # 初始化规则组存储
                if 'rule_groups' not in st.session_state:
                    st.session_state.rule_groups = {
                        '金叉死叉': {
                            'buy_rule': '(REF(SMA(close,5), 1) < REF(SMA(close,7), 1)) & (SMA(close,5) > SMA(close,7))',
                            'sell_rule': '(REF(SMA(close,5), 1) > REF(SMA(close,7), 1)) & (SMA(close,5) < SMA(close,7))'
                        }
                    }
                
                # 规则组管理
                st.subheader("规则组管理")
                selected_group = st.selectbox(
                    "选择规则组",
                    options=list(st.session_state.rule_groups.keys()),
                    key="rule_group_select"
                )
                
                if st.button("加载规则组"):
                    if selected_group in st.session_state.rule_groups:
                        group = st.session_state.rule_groups[selected_group]
                        st.session_state.buy_rule_expr = group['buy_rule']
                        st.session_state.sell_rule_expr = group['sell_rule']
                        st.rerun()
                
                if st.button("保存当前规则组"):
                    group_name = st.text_input("输入规则组名称", key="new_rule_group_name")
                    if group_name and group_name.strip():
                        st.session_state.rule_groups[group_name] = {
                            'buy_rule': st.session_state.get('buy_rule_expr', ''),
                            'sell_rule': st.session_state.get('sell_rule_expr', '')
                        }
                        st.success(f"规则组 '{group_name}' 已保存")
    
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
    # 使用session_state记住用户的上次设置
    if 'last_initial_capital' not in st.session_state:
        st.session_state.last_initial_capital = 100000
    if 'last_commission_rate' not in st.session_state:
        st.session_state.last_commission_rate = 0.03
    
    initial_capital = st.number_input("初始资金(元)", min_value=10000, value=st.session_state.last_initial_capital, key="initial_capital_input")
    commission_rate = st.number_input("交易佣金(%)", min_value=0.0, max_value=1.0, value=st.session_state.last_commission_rate, key="commission_rate_input")
    
    # 更新session_state中的值
    st.session_state.last_initial_capital = initial_capital
    st.session_state.last_commission_rate = commission_rate
    
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

        # 初始化回测参数BacktestConfig
        backtest_config = BacktestConfig( # 设置回测参数
            start_date=start_date.strftime("%Y%m%d"),  # BacktestConfig需要YYYYMMDD格式
            end_date=end_date.strftime("%Y%m%d"),
            frequency=frequency,
            target_symbol=symbol,
            initial_capital=initial_capital,
            commission=commission_rate / 100  # 将百分比转换为小数
        )
        
        # 初始化事件引擎BacktestEngine
        db = cast(DatabaseManager, st.session_state.db)
        data = await db.load_stock_data(symbol, start_date, end_date, frequency)  # 直接传递date对象
        engine = BacktestEngine(config=backtest_config, data=data)
        
        
        st.write("回测使用的数据") 
        st.write(data) 

        # 确保事件处理器能访问当前索引和方向
        def handle_schedule_with_index(event: StrategyScheduleEvent):
            event.current_index = engine.current_index
            return handle_schedule(event)
            
        def handle_signal_with_direction(event: StrategySignalEvent):
            event.direction = 'BUY' if event.confidence > 0 else 'SELL'
            return handle_signal(event)
            
        # 注册增强版的事件处理器（包含上下文信息）
        engine.register_handler(StrategyScheduleEvent, handle_schedule_with_index)
        engine.register_handler(StrategySignalEvent, handle_signal_with_direction)
        
        # 初始化策略
        if strategy == "月定投":
            fixed_strategy = FixedInvestmentStrategy(
                Data=data,
                name="月定投策略",
                buy_rule_expr="True",
                sell_rule_expr="False"
            )
            # 注册策略
            engine.register_strategy(fixed_strategy)
        elif strategy == "自定义规则" and ('buy_rule_expr' in st.session_state or 'sell_rule_expr' in st.session_state):
            from core.strategy.rule_based_strategy import RuleBasedStrategy
            
            # 指标服务初始化
            if 'indicator_service' not in st.session_state:
                from core.strategy.indicators import IndicatorService
                st.session_state.indicator_service = IndicatorService()
            
            # 实例化自定义策略
            rule_strategy = RuleBasedStrategy(
                Data=data,
                name="自定义规则策略",
                indicator_service=st.session_state.indicator_service,
                buy_rule_expr=st.session_state.get('buy_rule_expr', ""),
                sell_rule_expr=st.session_state.get('sell_rule_expr', "")
            )
            # 注册策略实例
            engine.register_strategy(rule_strategy)
        
        # 启动事件循环
        task_id = f"backtest_{st.session_state.strategy_id}" # 回测任务唯一id
        # progress_service.start_task(task_id, 100)
        
        # 进度管理机制（目前未生效）
        # for i in range(100):
        #     # time.sleep(0.1)  # 模拟回测过程
        #     progress_service.update_progress(task_id, (i + 1) / 100)
        
        engine.logger.debug("开始回测...")

        # 回测运行（engine中已有策略实例和所有数据）
        engine.run(pd.to_datetime(start_date), pd.to_datetime(end_date))
        # progress_service.end_task(task_id)
        
        # 获取回测结果
        results = engine.get_results()
        data = engine.data
        equity_data = engine.equity_records

        if results:
            st.success("回测完成！")
            engine.logger.debug("回测完成！")
            
            # 使用标签页组织显示内容
            tab1, tab2, tab3, tab4, tab5 = st.tabs(["回测摘要", "交易记录", "仓位明细", "净值曲线", "原始数据"])
            
            with tab1:
                # 格式化显示回测摘要
                st.subheader("📊 回测摘要")
                summary = results["summary"]
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("初始资金", f"¥{summary['initial_capital']:,.2f}")
                    st.metric("最终资金", f"¥{summary['final_capital']:,.2f}")
                    profit = summary['final_capital'] - summary['initial_capital']
                    profit_pct = (profit / summary['initial_capital']) * 100
                    st.metric("总收益", f"¥{profit:,.2f}", f"{profit_pct:.2f}%")
                
                with col2:
                    st.metric("总交易次数", summary['total_trades'])
                    win_rate_pct = summary['win_rate'] * 100
                    st.metric("胜率", f"{win_rate_pct:.2f}%")
                    st.metric("最大回撤", f"{summary['max_drawdown'] * 100:.2f}%")
                
                with col3:
                    # 计算年化收益率（简化计算）
                    if len(engine.equity_records) > 1:
                        days = (engine.equity_records['timestamp'].iloc[-1] - engine.equity_records['timestamp'].iloc[0]).days
                        if days > 0:
                            annual_return = (profit_pct / days) * 365
                            st.metric("年化收益率", f"{annual_return:.2f}%")
                        else:
                            st.metric("年化收益率", "N/A")
                    else:
                        st.metric("年化收益率", "N/A")
            
            with tab2:
                # 显示交易记录
                st.subheader("💱 交易记录")
                if results["trades"]:
                    trades_df = pd.DataFrame(results["trades"])
                    # 格式化时间显示
                    if 'timestamp' in trades_df.columns:
                        trades_df['timestamp'] = pd.to_datetime(trades_df['timestamp'])
                    st.dataframe(trades_df, use_container_width=True)
                    
                    # 交易统计
                    if not trades_df.empty:
                        st.subheader("交易统计")
                        buy_trades = trades_df[trades_df['direction'] == 'BUY']
                        sell_trades = trades_df[trades_df['direction'] == 'SELL']
                        
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("买入交易", len(buy_trades))
                        with col2:
                            st.metric("卖出交易", len(sell_trades))
                        with col3:
                            total_commission = trades_df['commission'].sum()
                            st.metric("总手续费", f"¥{total_commission:,.2f}")
                else:
                    st.info("暂无交易记录")
            
            with tab3:
                # 显示仓位明细
                st.subheader("📈 仓位明细")
                if not engine.equity_records.empty:
                    # 创建仓位历史表格
                    position_history = engine.equity_records.copy()
                    position_history['timestamp'] = pd.to_datetime(position_history['timestamp'])
                    
                    # 添加持仓价值计算
                    position_history['position_value'] = position_history['position'] * position_history['price']
                    position_history['position_pct'] = (position_history['position_value'] / position_history['total_value']) * 100
                    
                    # 格式化显示
                    display_cols = ['timestamp', 'price', 'position', 'position_value', 'position_pct', 'cash', 'total_value']
                    st.dataframe(position_history[display_cols], use_container_width=True)
                    
                    # 仓位统计
                    st.subheader("仓位统计")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        max_position = position_history['position'].max()
                        st.metric("最大持仓数量", f"{max_position:,.0f}")
                    with col2:
                        avg_position_pct = position_history['position_pct'].mean()
                        st.metric("平均仓位占比", f"{avg_position_pct:.2f}%")
                    with col3:
                        final_position = position_history['position'].iloc[-1]
                        st.metric("最终持仓", f"{final_position:,.0f}")
                else:
                    st.info("暂无仓位记录")
            
            with tab4:
                # 绘制净值曲线
                st.subheader("📈 净值曲线")
                
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
                
                if 'chart_service' not in st.session_state:
                    st.session_state.chart_service = init_chart_service(data, equity_data)
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

                chart_service.render_chart_controls()
                chart_service.render_chart_button(st.session_state[config_key])
            
            with tab5:
                # 显示原始数据
                st.subheader("📋 原始数据")
                st.dataframe(engine.data)
                
                # 显示买卖信号
                st.subheader("📶 买卖信号")
                signal_data = engine.data[['combined_time', 'close', 'signal']].copy()
                signal_data['signal_text'] = signal_data['signal'].map({0: '无信号', 1: '买入', -1: '卖出'})
                st.dataframe(signal_data, use_container_width=True)


        else:
            st.error("回测失败，请检查输入参数")
