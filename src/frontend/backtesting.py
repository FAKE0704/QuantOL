import streamlit as st
import pandas as pd
import plotly.express as px
from core.strategy.backtesting import  BacktestEngine
from core.strategy.backtesting import  BacktestConfig
from services.chart_service import  ChartService, DataBundle
from event_bus.event_types import StrategyScheduleEvent, StrategySignalEvent
from core.strategy.event_handlers import  handle_signal
from core.strategy.strategy import FixedInvestmentStrategy
from core.data.database import DatabaseManager
from services.progress_service import progress_service
from typing import cast
import time
from support.log.logger import logger

async def show_backtesting_page():
    # 初始化策略ID
    if 'strategy_id' not in st.session_state:
        import uuid
        st.session_state.strategy_id = str(uuid.uuid4())
    
    # 初始化回测配置对象
    if 'backtest_config' not in st.session_state:
        # 创建默认配置
        st.session_state.backtest_config = BacktestConfig(
            start_date="20250401",
            end_date="20250430",
            target_symbol="sh.600000",
            frequency="d",
            initial_capital=100000,
            commission_rate=0.0003,
            position_strategy_type="fixed_percent",
            position_strategy_params={"percent": 0.1}
        )

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
            index=20
        )
        
        # 更新配置对象中的股票代码
        if selected:
            st.session_state.backtest_config.target_symbol = selected[0]
    with col2:
        if st.button("🔄 刷新列表", help="点击手动更新股票列表", key="refresh_button"):
            if 'stock_cache' in st.session_state:
                del st.session_state.stock_cache
            st.rerun()
    
    # 时间范围选择
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("开始日期", key="start_date_input", value= "2025-04-01")
        # 更新配置对象中的开始日期
        st.session_state.backtest_config.start_date = start_date.strftime("%Y%m%d")
    with col2:
        end_date = st.date_input("结束日期", key="end_date_input")
        # 更新配置对象中的结束日期
        st.session_state.backtest_config.end_date = end_date.strftime("%Y%m%d")
    
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
        # 更新配置对象中的频率
        st.session_state.backtest_config.frequency = frequency
    
    

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
    # 更新配置对象中的初始资金
    st.session_state.backtest_config.initial_capital = initial_capital
    
    commission_rate = st.number_input("交易佣金(%)", min_value=0.0, max_value=1.0, value=st.session_state.last_commission_rate, key="commission_rate_input")
    # 更新配置对象中的佣金率（转换为小数）
    st.session_state.backtest_config.commission_rate = commission_rate / 100
    
    # 更新session_state中的值
    st.session_state.last_initial_capital = initial_capital
    st.session_state.last_commission_rate = commission_rate
    
    # 仓位策略配置
    st.subheader("📊 仓位策略配置")
    
    # 仓位策略类型选择
    position_strategy_type = st.selectbox(
        "仓位策略类型",
        options=["fixed_percent", "kelly"],
        format_func=lambda x: "固定比例" if x == "fixed_percent" else "凯利公式",
        key="position_strategy_select"
    )
    # 更新配置对象中的仓位策略类型
    st.session_state.backtest_config.position_strategy_type = position_strategy_type
    
    # 根据策略类型显示不同的参数配置
    if position_strategy_type == "fixed_percent":
        percent = st.slider(
            "固定仓位比例(%)",
            min_value=1,
            max_value=100,
            value=10,
            key="fixed_percent_slider"
        )
        # 更新配置对象中的仓位策略参数
        st.session_state.backtest_config.position_strategy_params = {"percent": percent / 100}
        
    elif position_strategy_type == "kelly":
        col1, col2, col3 = st.columns(3)
        with col1:
            win_rate = st.slider(
                "策略胜率(%)",
                min_value=1,
                max_value=99,
                value=50,
                key="kelly_win_rate"
            )
        with col2:
            win_loss_ratio = st.slider(
                "盈亏比",
                min_value=0.1,
                max_value=10.0,
                value=2.0,
                step=0.1,
                key="kelly_win_loss_ratio"
            )
        with col3:
            max_percent = st.slider(
                "最大仓位限制(%)",
                min_value=1,
                max_value=100,
                value=25,
                key="kelly_max_percent"
            )
        # 更新配置对象中的仓位策略参数
        st.session_state.backtest_config.position_strategy_params = {
            "win_rate": win_rate / 100,
            "win_loss_ratio": win_loss_ratio,
            "max_percent": max_percent / 100
        }
    
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
        # 使用存储在session_state中的配置对象
        backtest_config = st.session_state.backtest_config
        
        # 初始化事件引擎BacktestEngine
        db = cast(DatabaseManager, st.session_state.db)
        data = await db.load_stock_data(backtest_config.target_symbol, start_date, end_date, backtest_config.frequency)  # 直接传递date对象
        engine = BacktestEngine(config=backtest_config, data=data)
        
        
        st.write("回测使用的数据") 
        st.write(data) 

        # 确保事件处理器能访问当前索引和方向
        # def handle_schedule_with_index(event: StrategyScheduleEvent):
        #     event.current_index = engine.current_index
        #     return handle_schedule(event)
            
        def handle_signal_with_direction(event: StrategySignalEvent):
            event.direction = 'BUY' if event.confidence > 0 else 'SELL'
            return handle_signal(event)
            
        # 注册增强版的事件处理器（包含上下文信息）
        # engine.register_handler(StrategyScheduleEvent, handle_schedule_with_index)
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
        
        logger.debug("开始回测...")

        # 回测运行（engine中已有策略实例和所有数据）
        engine.run(pd.to_datetime(start_date), pd.to_datetime(end_date))
        # progress_service.end_task(task_id)
        
        # 获取回测结果
        results = engine.get_results()
        data = engine.data
        equity_data = engine.equity_records

        if results:
            st.success("回测完成！")
            logger.debug("回测完成！")
            
            # 使用标签页组织显示内容
            tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
                "回测摘要", "交易记录", "仓位明细", "净值曲线", "原始数据", "自定义图表", "仓位策略"
            ])
            
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
                # 显示仓位明细 - 使用PortfolioManager获取持仓信息
                st.subheader("📈 仓位明细")
                
                # 获取当前持仓信息
                portfolio_manager = engine.portfolio_manager
                all_positions = portfolio_manager.get_all_positions()
                
                if all_positions:
                    # 创建持仓信息表格
                    position_data = []
                    for symbol, position in all_positions.items():
                        position_data.append({
                            '标的代码': symbol,
                            '持仓数量': position.quantity,
                            '平均成本': position.avg_cost,
                            '当前价值': position.current_value,
                            '当前价格': position.stock.last_price if hasattr(position.stock, 'last_price') else 0
                        })
                    
                    positions_df = pd.DataFrame(position_data)
                    
                    # 计算持仓权重
                    total_value = portfolio_manager.get_portfolio_value()
                    if total_value > 0:
                        positions_df['持仓权重'] = (positions_df['当前价值'] / total_value) * 100
                    
                    st.dataframe(positions_df, use_container_width=True)
                    
                    # 仓位统计
                    st.subheader("仓位统计")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        total_position_value = positions_df['当前价值'].sum()
                        st.metric("持仓总价值", f"¥{total_position_value:,.2f}")
                    with col2:
                        cash_balance = portfolio_manager.get_cash_balance()
                        st.metric("现金余额", f"¥{cash_balance:,.2f}")
                    with col3:
                        portfolio_value = portfolio_manager.get_portfolio_value()
                        st.metric("组合总价值", f"¥{portfolio_value:,.2f}")
                        
                    # 持仓分布饼图
                    if not positions_df.empty and total_value > 0:
                        st.subheader("持仓分布")
                        fig = px.pie(positions_df, values='当前价值', names='标的代码', 
                                    title='持仓价值分布')
                        st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("暂无持仓记录")
                    
                    # 显示现金信息
                    cash_balance = portfolio_manager.get_cash_balance()
                    portfolio_value = portfolio_manager.get_portfolio_value()
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("现金余额", f"¥{cash_balance:,.2f}")
                    with col2:
                        st.metric("组合总价值", f"¥{portfolio_value:,.2f}")
            
            with tab4:
                st.subheader("📈 净值曲线")

            
            with tab5:
                # 显示原始数据
                st.subheader("📋 原始数据")
                st.dataframe(engine.data)
                
                # 显示买卖信号
                st.subheader("📶 买卖信号")
                signal_data = engine.data.loc[engine.data['signal']!=0,['combined_time', 'close', 'signal']].copy()
                signal_data['signal_text'] = signal_data['signal'].map({0: '无信号', 1: '买入', -1: '卖出'})
                st.dataframe(signal_data, use_container_width=True)
            with tab6:
                # 绘制净值曲线
                st.subheader("📈 自定义图表")
                
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
            
            with tab7:
                # 显示仓位策略配置信息
                st.subheader("📊 仓位策略配置")
                
                if 'position_strategy_config' in results:
                    strategy_config = results['position_strategy_config']
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.metric("策略类型", 
                                 "固定比例" if strategy_config['type'] == 'fixed_percent' else "凯利公式")
                        
                        # 显示具体参数
                        st.subheader("策略参数")
                        params = strategy_config['params']
                        
                        if strategy_config['type'] == 'fixed_percent':
                            percent = params.get('percent', 0.1) * 100
                            st.metric("固定仓位比例", f"{percent:.1f}%")
                            
                        elif strategy_config['type'] == 'kelly':
                            win_rate = params.get('win_rate', 0.5) * 100
                            win_loss_ratio = params.get('win_loss_ratio', 2.0)
                            max_percent = params.get('max_percent', 0.25) * 100
                            
                            st.metric("策略胜率", f"{win_rate:.1f}%")
                            st.metric("盈亏比", f"{win_loss_ratio:.2f}")
                            st.metric("最大仓位限制", f"{max_percent:.1f}%")
                    
                    with col2:
                        # 显示策略说明
                        st.subheader("策略说明")
                        if strategy_config['type'] == 'fixed_percent':
                            st.info("""
                            **固定比例仓位策略**
                            - 每次交易使用固定比例的资金
                            - 简单易用，风险控制稳定
                            - 适合趋势跟踪和震荡策略
                            """)
                        else:
                            st.info("""
                            **凯利公式仓位策略**
                            - 根据策略胜率和盈亏比动态调整仓位
                            - 理论上最优的资金管理方法
                            - 适合高胜率或高盈亏比的策略
                            """)
                    
                    # 显示策略性能影响分析
                    st.subheader("策略性能影响")
                    
                    # 计算仓位策略对交易的影响
                    if results["trades"]:
                        trades_df = pd.DataFrame(results["trades"])
                        if not trades_df.empty:
                            # 计算平均单笔交易金额占比
                            total_trades = len(trades_df)
                            total_investment = abs(trades_df['total_cost'].sum())
                            avg_trade_amount = total_investment / total_trades if total_trades > 0 else 0
                            avg_position_pct = (avg_trade_amount / summary['initial_capital']) * 100
                            
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("平均单笔交易金额", f"¥{avg_trade_amount:,.0f}")
                            with col2:
                                st.metric("平均仓位占比", f"{avg_position_pct:.2f}%")
                            with col3:
                                # 计算仓位利用率
                                max_position_value = engine.equity_records['position_value'].max() if 'position_value' in engine.equity_records.columns else 0
                                position_utilization = (max_position_value / summary['initial_capital']) * 100
                                st.metric("最大仓位利用率", f"{position_utilization:.2f}%")
                else:
                    st.info("暂无仓位策略配置信息")

        else:
            st.error("回测失败，请检查输入参数")
