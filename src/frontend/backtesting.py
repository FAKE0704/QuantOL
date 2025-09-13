import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
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

    # 初始化规则组
    if 'rule_groups' not in st.session_state:
        st.session_state.rule_groups = {
            '金叉死叉': {
                'buy_rule': '(REF(SMA(close,5), 1) < REF(SMA(close,7), 1)) & (SMA(close,5) > SMA(close,7))',
                'sell_rule': '(REF(SMA(close,5), 1) > REF(SMA(close,7), 1)) & (SMA(close,5) < SMA(close,7))'
            },
            '相对强度': {
                'buy_rule': '(REF(RSI(close,5), 1) < 30) & (RSI(close,5) >= 30)',
                'sell_rule': '(REF(RSI(close,5), 1) >= 60) & (RSI(close,5) < 60)'
            },
            'Martingale': {
                'open_rule': '(close < REF(SMA(close,5), 1)) & (close > SMA(close,5))',  # 价格上穿5线开仓
                'close_rule': '(close - (COST/POSITION))/(COST/POSITION) * 100 >= 5',  # 价格上涨5%时清仓
                'buy_rule': '(close - (COST/POSITION))/(COST/POSITION) * 100 <= -5',   # 价格下跌5%时加仓
                'sell_rule': ''    # 只清仓不平仓
            }
        }

    st.title("策略回测")

    # 使用标签页组织配置
    config_tab1, config_tab2, config_tab3 = st.tabs(["📊 回测范围", "⚙️ 策略配置", "📈 仓位配置"])

    with config_tab1:
        st.subheader("📊 回测范围")
        # 股票选择
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

            # 选择股票组件，支持单选、多选
            selected_options = st.multiselect(
                "选择股票（可多选）",
                options=st.session_state.stock_cache,
                format_func=lambda x: f"{x[0]} {x[1]}",
                help="选择股票进行组合回测",
                key="stock_select",
                default=[st.session_state.stock_cache[20]] if st.session_state.stock_cache else []
            )

            # 更新配置对象中的股票代码
            if selected_options:
                selected_symbols = [symbol[0] for symbol in selected_options]
                # 使用统一接口设置符号
                st.session_state.backtest_config.target_symbols = selected_symbols

            # 显示已选股票
            if selected_options:
                st.info(f"已选择 {len(selected_options)} 只股票: {', '.join([f'{s[0]}' for s in selected_options])}")

        with col2:
            if st.button("🔄 刷新列表", help="点击手动更新股票列表", key="refresh_button"):
                if 'stock_cache' in st.session_state:
                    del st.session_state.stock_cache
                st.rerun()

        # 时间范围选择
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("开始日期", key="start_date_input_global", value= "2025-04-01")
            # 更新配置对象中的开始日期
            st.session_state.backtest_config.start_date = start_date.strftime("%Y%m%d")
        with col2:
            end_date = st.date_input("结束日期", key="end_date_input_global")
            # 更新配置对象中的结束日期
            st.session_state.backtest_config.end_date = end_date.strftime("%Y%m%d")

        # 频率选择
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
            format_func=lambda x: frequency_options[x],
            key="frequency_select_global"
        )
        # 更新配置对象中的频率
        st.session_state.backtest_config.frequency = frequency

    with config_tab2:
        st.subheader("⚙️ 策略配置")

        # 默认策略配置
        st.write("**默认策略配置**")
        default_strategy_type = st.selectbox(
            "默认策略类型",
            options=["月定投", "移动平均线交叉", "MACD交叉", "RSI超买超卖", "自定义规则"],
            key="default_strategy_type"
        )

        # 如果默认策略是自定义规则，显示规则编辑器和规则组管理
        if default_strategy_type == "自定义规则":
            # 规则编辑器
            with st.expander("默认规则编辑器", expanded=True):
                cols = st.columns([3, 1])

                with cols[0]:
                    # 使用加载的规则值或默认值
                    open_rule_value = st.session_state.get("loaded_open_rule", st.session_state.get("default_open_rule", ""))
                    close_rule_value = st.session_state.get("loaded_close_rule", st.session_state.get("default_close_rule", ""))
                    buy_rule_value = st.session_state.get("loaded_buy_rule", st.session_state.get("default_buy_rule", ""))
                    sell_rule_value = st.session_state.get("loaded_sell_rule", st.session_state.get("default_sell_rule", ""))

                    st.subheader("开仓规则")
                    st.text_area(
                        "默认开仓条件",
                        value=open_rule_value,
                        height=60,
                        key="default_open_rule_editor",
                        help="输入默认开仓条件表达式"
                    )

                    st.subheader("清仓规则")
                    st.text_area(
                        "默认清仓条件",
                        value=close_rule_value,
                        height=60,
                        key="default_close_rule_editor",
                        help="输入默认清仓条件表达式"
                    )

                    st.subheader("加仓规则")
                    st.text_area(
                        "默认加仓条件",
                        value=buy_rule_value,
                        height=60,
                        key="default_buy_rule_editor",
                        help="输入默认开仓条件表达式"
                    )

                    st.subheader("平仓规则")
                    st.text_area(
                        "默认平仓条件",
                        value=sell_rule_value,
                        height=60,
                        key="default_sell_rule_editor",
                        help="输入默认平仓条件表达式"
                    )

                with cols[1]:
                    st.subheader("规则语法校验")

                    # 统一的规则校验函数
                    def validate_rule(rule_key, display_name):
                        if rule_key in st.session_state and st.session_state[rule_key]:
                            from core.strategy.rule_parser import RuleParser
                            valid, msg = RuleParser.validate_syntax(st.session_state[rule_key])
                            if valid:
                                st.success(f"✓ {display_name}语法正确")
                                st.code(f"{display_name}: {st.session_state[rule_key]}")
                            else:
                                st.error(f"{display_name}错误: {msg}")

                    # 校验所有规则
                    validate_rule("default_open_rule_editor", "默认开仓")
                    validate_rule("default_close_rule_editor", "默认清仓")
                    validate_rule("default_buy_rule_editor", "默认加仓")
                    validate_rule("default_sell_rule_editor", "默认平仓")

                    if not any([st.session_state.get('default_open_rule_editor'), st.session_state.get('default_close_rule_editor'),
                              st.session_state.get('default_buy_rule_editor'), st.session_state.get('default_sell_rule_editor')]):
                        st.info("请输入默认开仓/清仓/加仓/平仓规则表达式")

                    # 规则组管理
                    st.subheader("规则组管理")

                    # 检查是否有规则组可用
                    if st.session_state.rule_groups:
                        selected_group = st.selectbox(
                            "选择规则组",
                            options=list(st.session_state.rule_groups.keys()),
                            key="default_rule_group_select"
                        )

                        # 使用key来获取当前选择的规则组
                        if st.button("加载规则组到默认策略", key="load_rule_group_button"):
                            # 获取当前选择的规则组
                            current_selected_group = st.session_state.default_rule_group_select
                            if current_selected_group in st.session_state.rule_groups:
                                group = st.session_state.rule_groups[current_selected_group]
                                # 使用唯一key重新创建规则编辑器
                                st.session_state.rule_group_loaded = True
                                st.session_state.loaded_open_rule = group.get('open_rule', '')
                                st.session_state.loaded_close_rule = group.get('close_rule', '')
                                st.session_state.loaded_buy_rule = group.get('buy_rule', '')
                                st.session_state.loaded_sell_rule = group.get('sell_rule', '')
                                st.rerun()
                    else:
                        st.info("暂无规则组，请先创建规则组")

                    if st.button("保存当前为规则组"):
                        group_name = st.text_input("输入规则组名称", key="default_new_rule_group_name")
                        if group_name and group_name.strip():
                            st.session_state.rule_groups[group_name] = {
                                'open_rule': st.session_state.get('default_open_rule_editor', ''),
                                'close_rule': st.session_state.get('default_close_rule_editor', ''),
                                'buy_rule': st.session_state.get('default_buy_rule_editor', ''),
                                'sell_rule': st.session_state.get('default_sell_rule_editor', '')
                            }
                            st.success(f"规则组 '{group_name}' 已保存")
                            st.rerun()

        # 策略映射配置（多股票选择时才显示）
        if len(selected_options) > 1:

            # 初始化策略映射
            if 'strategy_mapping' not in st.session_state:
                st.session_state.strategy_mapping = {}

            # 为每个股票配置策略
            st.write("**各股票策略配置**")
            for symbol_option in selected_options:
                symbol = symbol_option[0]
                symbol_name = symbol_option[1]

                # 为每个股票创建扩展器来配置策略
                with st.expander(f"{symbol} - {symbol_name}", expanded=False):
                    col1, col2 = st.columns([1, 1])

                    with col1:
                        # 生成规则组选项
                        rule_group_options = []
                        if 'rule_groups' in st.session_state and st.session_state.rule_groups:
                            rule_group_options = [f"规则组: {name}" for name in st.session_state.rule_groups.keys()]

                        # 策略选择
                        strategy_choice = st.selectbox(
                            f"选择策略类型",
                            options=["使用默认策略", "月定投", "移动平均线交叉", "MACD交叉", "RSI超买超卖", "自定义规则"] + rule_group_options,
                            key=f"strategy_type_{symbol}"
                        )

                    with col2:
                        # 显示当前策略状态
                        if strategy_choice == "使用默认策略":
                            st.info("使用默认策略配置")
                        elif strategy_choice.startswith("规则组:"):
                            group_name = strategy_choice.replace("规则组: ", "")
                            st.success(f"使用规则组: {group_name}")
                        else:
                            st.success(f"使用自定义策略: {strategy_choice}")

                    # 如果选择自定义规则，显示规则编辑器
                    if strategy_choice == "自定义规则":
                        st.text_area(
                            f"开仓条件 - {symbol}",
                            value=st.session_state.get(f"open_rule_{symbol}", ""),
                            height=60,
                            key=f"open_rule_{symbol}",
                            help="输入开仓条件表达式"
                        )
                        st.text_area(
                            f"清仓条件 - {symbol}",
                            value=st.session_state.get(f"close_rule_{symbol}", ""),
                            height=60,
                            key=f"close_rule_{symbol}",
                            help="输入清仓条件表达式"
                        )
                        st.text_area(
                            f"加仓条件 - {symbol}",
                            value=st.session_state.get(f"buy_rule_{symbol}", ""),
                            height=60,
                            key=f"buy_rule_{symbol}",
                            help="输入加仓条件表达式"
                        )
                        st.text_area(
                            f"平仓条件 - {symbol}",
                            value=st.session_state.get(f"sell_rule_{symbol}", ""),
                            height=60,
                            key=f"sell_rule_{symbol}",
                            help="输入平仓条件表达式"
                        )

                    # 存储策略映射
                    if strategy_choice != "使用默认策略":
                        if strategy_choice.startswith("规则组:"):
                            # 处理规则组选择
                            group_name = strategy_choice.replace("规则组: ", "")
                            if 'rule_groups' in st.session_state and group_name in st.session_state.rule_groups:
                                group = st.session_state.rule_groups[group_name]
                                st.session_state.strategy_mapping[symbol] = {
                                    'type': "自定义规则",
                                    'buy_rule': group.get('buy_rule', ''),
                                    'sell_rule': group.get('sell_rule', ''),
                                    'open_rule': group.get('open_rule', ''),
                                    'close_rule': group.get('close_rule', '')
                                }
                                # 同时更新session state中的规则值，以便在界面上显示
                                st.session_state[f"buy_rule_{symbol}"] = group.get('buy_rule', '')
                                st.session_state[f"sell_rule_{symbol}"] = group.get('sell_rule', '')
                                st.session_state[f"open_rule_{symbol}"] = group.get('open_rule', '')
                                st.session_state[f"close_rule_{symbol}"] = group.get('close_rule', '')
                        else:
                            # 处理普通策略选择
                            st.session_state.strategy_mapping[symbol] = {
                                'type': strategy_choice,
                                'buy_rule': st.session_state.get(f"buy_rule_{symbol}", ""),
                                'sell_rule': st.session_state.get(f"sell_rule_{symbol}", ""),
                                'open_rule': st.session_state.get(f"open_rule_{symbol}", ""),
                                'close_rule': st.session_state.get(f"close_rule_{symbol}", "")
                            }
                    elif symbol in st.session_state.strategy_mapping:
                        del st.session_state.strategy_mapping[symbol]

            # 更新配置对象中的策略映射
            st.session_state.backtest_config.strategy_mapping = st.session_state.strategy_mapping
            st.session_state.backtest_config.default_strategy = {
                'type': default_strategy_type,
                'buy_rule': st.session_state.get("default_buy_rule_editor", ""),
                'sell_rule': st.session_state.get("default_sell_rule_editor", ""),
                'open_rule': st.session_state.get("default_open_rule_editor", ""),
                'close_rule': st.session_state.get("default_close_rule_editor", "")
            }

    with config_tab3:
        st.subheader("📈 仓位配置")

        # 仓位策略类型选择
        position_strategy_type = st.selectbox(
            "仓位策略类型",
            options=["fixed_percent", "kelly", "martingale"],
            format_func=lambda x: "固定比例" if x == "fixed_percent" else "凯利公式" if x == "kelly" else "马丁策略",
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

        elif position_strategy_type == "martingale":
            col1, col2 = st.columns(2)
            with col1:
                initial_ratio = st.slider(
                    "初始开仓资金比例(%)",
                    min_value=1.0,
                    max_value=10.0,
                    value=0.01,
                    step=0.01,
                    key="martingale_initial_ratio"
                )
            with col2:
                multiplier = st.slider(
                    "加仓倍数",
                    min_value=1.0,
                    max_value=10.0,
                    value=2.0,
                    step=0.1,
                    key="martingale_multiplier"
                )

            # 显示仓位计算示例
            st.info(f"仓位计算示例: 第1次开仓 {initial_ratio}%, 第2次加仓 {initial_ratio * multiplier:.1f}%, 第3次加仓 {initial_ratio * multiplier**2:.1f}%")

            # 更新配置对象中的仓位策略参数
            st.session_state.backtest_config.position_strategy_params = {
                "initial_ratio": initial_ratio / 100,
                "multiplier": multiplier,
                "clear_on_insufficient": True  # 资金不足时清仓
            }
    
    
    

    
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
        
        # 统一数据加载
        symbols = backtest_config.get_symbols()
        
        if backtest_config.is_multi_symbol():
            # 多符号模式
            data = await st.session_state.db.load_multiple_stock_data(
                symbols, start_date, end_date, backtest_config.frequency
            )
            st.info(f"已加载 {len(data)} 只股票数据")
        else:
            # 单符号模式
            data = await st.session_state.db.load_stock_data(
                symbols[0], start_date, end_date, backtest_config.frequency
            )

        
        engine = BacktestEngine(config=backtest_config, data=data)
        
        
        st.write("回测使用的数据") 
        st.write(data) 

        # 确保事件处理器能访问当前索引和方向
        # def handle_schedule_with_index(event: StrategyScheduleEvent):
        #     event.current_index = engine.current_index
        #     return handle_schedule(event)
            
        def handle_signal_with_direction(event: StrategySignalEvent):
            # 保持向后兼容性：如果使用旧的direction方式，自动设置signal_type
            if not hasattr(event, 'signal_type') or event.signal_type is None:
                from core.strategy.signal_types import SignalType
                event.signal_type = SignalType.BUY if event.confidence > 0 else SignalType.SELL
            return handle_signal(event)
            
        # 注册增强版的事件处理器（包含上下文信息）
        # engine.register_handler(StrategyScheduleEvent, handle_schedule_with_index)
        engine.register_handler(StrategySignalEvent, handle_signal_with_direction)
        
        # 使用新的策略映射系统初始化策略
        from core.strategy.rule_based_strategy import RuleBasedStrategy
        from core.strategy.strategy import FixedInvestmentStrategy

        # 指标服务初始化
        if 'indicator_service' not in st.session_state:
            from core.strategy.indicators import IndicatorService
            st.session_state.indicator_service = IndicatorService()

        if backtest_config.is_multi_symbol():
            # 多符号模式：为每个符号创建独立的策略实例
            for symbol, symbol_data in data.items():
                # 获取该符号的策略配置
                symbol_strategy_config = backtest_config.get_strategy_for_symbol(symbol)
                strategy_type = symbol_strategy_config.get('type', '使用默认策略')

                if strategy_type == "月定投":
                    # 创建月定投策略
                    fixed_strategy = FixedInvestmentStrategy(
                        Data=symbol_data,
                        name=f"月定投策略_{symbol}",
                        buy_rule_expr="True",
                        sell_rule_expr="False"
                    )
                    engine.register_strategy(fixed_strategy)
                elif strategy_type == "自定义规则":
                    # 创建自定义规则策略
                    rule_strategy = RuleBasedStrategy(
                        Data=symbol_data,
                        name=f"自定义规则策略_{symbol}",
                        indicator_service=st.session_state.indicator_service,
                        buy_rule_expr=symbol_strategy_config.get('buy_rule', ''),
                        sell_rule_expr=symbol_strategy_config.get('sell_rule', ''),
                        open_rule_expr=symbol_strategy_config.get('open_rule', ''),
                        close_rule_expr=symbol_strategy_config.get('close_rule', ''),
                        portfolio_manager=engine.portfolio_manager
                    )
                    engine.register_strategy(rule_strategy)
                elif strategy_type.startswith("规则组:"):
                    # 处理规则组策略
                    group_name = strategy_type.replace("规则组: ", "")
                    if 'rule_groups' in st.session_state and group_name in st.session_state.rule_groups:
                        group = st.session_state.rule_groups[group_name]
                        rule_strategy = RuleBasedStrategy(
                            Data=symbol_data,
                            name=f"规则组策略_{symbol}_{group_name}",
                            indicator_service=st.session_state.indicator_service,
                            buy_rule_expr=group.get('buy_rule', ''),
                            sell_rule_expr=group.get('sell_rule', ''),
                            open_rule_expr=group.get('open_rule', ''),
                            close_rule_expr=group.get('close_rule', ''),
                            portfolio_manager=engine.portfolio_manager
                        )
                        engine.register_strategy(rule_strategy)
        else:
            # 单符号模式（保持向后兼容）
            default_strategy = backtest_config.default_strategy
            strategy_type = default_strategy.get('type', '使用默认策略')

            if strategy_type == "月定投":
                fixed_strategy = FixedInvestmentStrategy(
                    Data=data,
                    name="月定投策略",
                    buy_rule_expr="True",
                    sell_rule_expr="False"
                )
                engine.register_strategy(fixed_strategy)
            elif strategy_type == "自定义规则":
                rule_strategy = RuleBasedStrategy(
                    Data=data,
                    name="自定义规则策略",
                    indicator_service=st.session_state.indicator_service,
                    buy_rule_expr=default_strategy.get('buy_rule', ''),
                    sell_rule_expr=default_strategy.get('sell_rule', ''),
                    open_rule_expr=default_strategy.get('open_rule', ''),
                    close_rule_expr=default_strategy.get('close_rule', ''),
                    portfolio_manager=engine.portfolio_manager
                )
                engine.register_strategy(rule_strategy)
        
        # 启动事件循环
        task_id = f"backtest_{st.session_state.strategy_id}" # 回测任务唯一id
        # progress_service.start_task(task_id, 100)
        
        # 进度管理机制（目前未生效）
        # for i in range(100):
        #     # time.sleep(0.1)  # 模拟回测过程
        #     progress_service.update_progress(task_id, (i + 1) / 100)

        # 回测运行（engine中已有策略实例和所有数据）
        if backtest_config.is_multi_symbol():
            # 多符号回测
            engine.run_multi_symbol(pd.to_datetime(start_date), pd.to_datetime(end_date))
        else:
            # 单符号回测
            engine.run(pd.to_datetime(start_date), pd.to_datetime(end_date))
        # progress_service.end_task(task_id)
        
        # 获取回测结果
        results = engine.get_results()
        data = engine.data
        
        # 处理多符号和单符号的净值数据
        if "combined_equity" in results:
            # 多符号模式
            equity_data = results["combined_equity"]
            individual_results = results["individual"]
        else:
            # 单符号模式
            equity_data = pd.DataFrame(results["equity_records"])

        # 初始化ChartService（在所有标签页之前）
        @st.cache_resource(ttl=3600, show_spinner=False)
        def init_chart_service(raw_data, transaction_data):
            if isinstance(raw_data, dict):
                # 多符号模式：使用第一个符号的数据作为主数据
                first_symbol = next(iter(raw_data.keys()))
                raw_data = raw_data[first_symbol]
            
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

        if results:
            st.success("回测完成！")
            
            # 使用标签页组织显示内容
            tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
                "回测摘要", "交易记录", "仓位明细", "净值曲线", "原始数据", "自定义图表", "仓位策略", "策略配置"
            ])
            
            with tab1:
                # 格式化显示回测摘要
                st.subheader("📊 回测摘要")
                
                if "combined_equity" in results:
                    # 多符号模式
                    st.info(f"组合回测 - {len(backtest_config.get_symbols())} 只股票")
                    
                    # 计算组合性能指标
                    combined_equity = results["combined_equity"]
                    initial_capital = backtest_config.initial_capital
                    final_capital = combined_equity['total_value'].iloc[-1] if not combined_equity.empty else initial_capital
                    profit = final_capital - initial_capital
                    profit_pct = (profit / initial_capital) * 100
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("初始资金", f"¥{initial_capital:,.2f}")
                        st.metric("最终资金", f"¥{final_capital:,.2f}")
                        st.metric("总收益", f"¥{profit:,.2f}", f"{profit_pct:.2f}%")
                    
                    with col2:
                        total_trades = len(results["trades"])
                        st.metric("总交易次数", total_trades)
                        # 简化显示，多符号模式下胜率计算较复杂
                        st.metric("胜率", "多符号模式")
                        st.metric("最大回撤", "多符号模式")
                    
                    with col3:
                        # 计算年化收益率
                        if len(combined_equity) > 1:
                            days = (combined_equity['timestamp'].iloc[-1] - combined_equity['timestamp'].iloc[0]).days
                            if days > 0:
                                annual_return = (profit_pct / days) * 365
                                st.metric("年化收益率", f"{annual_return:.2f}%")
                            else:
                                st.metric("年化收益率", "N/A")
                        else:
                            st.metric("年化收益率", "N/A")
                    
                    # 显示各股票表现
                    st.subheader("各股票表现")
                    for symbol, symbol_results in results["individual"].items():
                        symbol_summary = symbol_results["summary"]
                        symbol_capital = backtest_config.get_symbol_capital(symbol)
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric(f"{symbol} 分配资金", f"¥{symbol_capital:,.2f}")
                        with col2:
                            st.metric(f"{symbol} 最终资金", f"¥{symbol_summary['final_capital']:,.2f}")
                        with col3:
                            symbol_profit = symbol_summary['final_capital'] - symbol_capital
                            symbol_profit_pct = (symbol_profit / symbol_capital) * 100
                            st.metric(f"{symbol} 收益", f"¥{symbol_profit:,.2f}", f"{symbol_profit_pct:.2f}%")
                
                else:
                    # 单符号模式
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
                        if len(equity_data) > 1:
                            days = (equity_data['timestamp'].iloc[-1] - equity_data['timestamp'].iloc[0]).days
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
                    
                    # 获取PortfolioManager实例（通过IPortfolio接口）
                    portfolio_manager = engine.portfolio_manager
                    
                    # 直接使用交易记录中已经包含的现金和持仓信息
                    enhanced_trades_df = trades_df.copy()
                    st.dataframe(enhanced_trades_df, use_container_width=True)
                    
                    # 交易统计
                    if not enhanced_trades_df.empty:
                        st.subheader("交易统计")
                        buy_trades = enhanced_trades_df[enhanced_trades_df['direction'] == 'BUY']
                        sell_trades = enhanced_trades_df[enhanced_trades_df['direction'] == 'SELL']
                        
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("买入交易", len(buy_trades))
                        with col2:
                            st.metric("卖出交易", len(sell_trades))
                        with col3:
                            total_commission = enhanced_trades_df['commission'].sum()
                            st.metric("总手续费", f"¥{total_commission:,.2f}")
                        with col4:
                            # 显示当前现金和持仓状态
                            current_cash = portfolio_manager.get_cash_balance()
                            current_positions = portfolio_manager.get_portfolio_value() - current_cash
                            st.metric("当前现金/持仓", f"¥{current_cash:,.0f}/¥{current_positions:,.0f}")
                            
                    # 如果交易记录中没有现金和持仓信息，显示提示
                    if 'cash_before' not in enhanced_trades_df.columns:
                        st.warning("⚠️ 交易记录中缺少现金和持仓信息，请更新BacktestEngine版本")
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
                
                # 检查净值数据是否存在
                if equity_data is not None and not equity_data.empty:
                    
                    if "combined_equity" in results:
                        # 多符号模式 - 使用子图显示各股票净值曲线
                        combined_equity = results["combined_equity"]
                        
                        # 确保时间列是datetime类型
                        combined_equity = combined_equity.copy()
                        combined_equity['timestamp'] = pd.to_datetime(combined_equity['timestamp'])
                        combined_equity = combined_equity.sort_values('timestamp')
                        
                        # 创建子图
                        
                        # 计算行数：1行组合净值 + N行个股净值
                        num_symbols = len(backtest_config.target_symbols)
                        fig = make_subplots(
                            rows=num_symbols + 1, cols=1,
                            subplot_titles=["组合净值"] + [f"{symbol} 净值" for symbol in backtest_config.target_symbols],
                            vertical_spacing=0.05
                        )
                        
                        # 添加组合净值曲线
                        fig.add_trace(
                            go.Scatter(x=combined_equity['timestamp'], y=combined_equity['total_value'], 
                                      name="组合净值", line=dict(color='blue')),
                            row=1, col=1
                        )
                        
                        # 添加各股票净值曲线
                        for i, symbol in enumerate(backtest_config.target_symbols, 2):
                            if symbol in combined_equity.columns:
                                fig.add_trace(
                                    go.Scatter(x=combined_equity['timestamp'], y=combined_equity[symbol], 
                                              name=f"{symbol} 净值", line=dict(color='green')),
                                    row=i, col=1
                                )
                        
                        fig.update_layout(height=300 * (num_symbols + 1), showlegend=True)
                        fig.update_xaxes(title_text="时间", row=num_symbols + 1, col=1)
                        fig.update_yaxes(title_text="净值", row=(num_symbols + 2) // 2, col=1)
                        
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # 显示组合净值统计
                        initial_value = combined_equity['total_value'].iloc[0]
                        final_value = combined_equity['total_value'].iloc[-1]
                        total_return = final_value - initial_value
                        total_return_pct = (total_return / initial_value) * 100
                        
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("组合初始净值", f"¥{initial_value:,.2f}")
                        with col2:
                            st.metric("组合最终净值", f"¥{final_value:,.2f}")
                        with col3:
                            st.metric("组合总收益率", f"{total_return_pct:.2f}%", f"¥{total_return:,.2f}")
                        
                    else:
                        # 单符号模式
                        equity_col = 'total_value'
                        timestamp_col = 'timestamp'
                        
                        if equity_col and timestamp_col:
                            # 确保时间列是datetime类型
                            equity_data = equity_data.copy()
                            logger.debug(f"净值数据行数{equity_data.shape[0]}")
                            equity_data[timestamp_col] = pd.to_datetime(equity_data[timestamp_col])
                            
                            # 按时间排序
                            equity_data = equity_data.sort_values(timestamp_col)
                            
                            # 计算收益率
                            initial_value = equity_data[equity_col].iloc[0]
                            equity_data['return_pct'] = ((equity_data[equity_col] - initial_value) / initial_value) * 100
                            
                            # 使用新的资产配置图表方法
                            fig = st.session_state.chart_service.draw_equity_and_allocation(equity_data)
                            
                            # 显示图表
                            st.plotly_chart(fig, use_container_width=True)
                            
                            # 显示净值统计信息
                            final_value = equity_data[equity_col].iloc[-1]
                            total_return = final_value - initial_value
                            total_return_pct = (total_return / initial_value) * 100
                            
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("初始净值", f"¥{initial_value:,.2f}")
                            with col2:
                                st.metric("最终净值", f"¥{final_value:,.2f}")
                            with col3:
                                st.metric("总收益率", f"{total_return_pct:.2f}%", f"¥{total_return:,.2f}")
                            
                            # 显示净值数据表格
                            with st.expander("查看净值数据明细"):
                                st.dataframe(equity_data[[timestamp_col, equity_col, 'return_pct']].rename(
                                    columns={
                                        timestamp_col: '时间',
                                        equity_col: '净值',
                                        'return_pct': '收益率%'
                                    }), use_container_width=True)
                        else:
                            st.error("❌ 净值数据格式错误，无法显示净值曲线")
                            st.warning("无法识别净值数据列名，请检查数据格式")
                            st.write("可用列名:", equity_data.columns.tolist())
                            st.write("前5行数据:")
                            st.dataframe(equity_data.head())
                            
                            # 提供调试信息
                            st.info("调试信息:")
                            st.write(f"净值数据形状: {equity_data.shape}")
                            st.write(f"净值数据类型: {type(equity_data)}")
                            if hasattr(equity_data, 'columns'):
                                st.write("列名详情:")
                                for col in equity_data.columns:
                                    st.write(f"- {col}: {equity_data[col].dtype}")
                else:
                    st.error("❌ 净值数据不存在或为空，无法显示净值曲线")
                    st.info("可能的原因:")
                    st.write("1. 回测过程中没有记录净值历史")
                    st.write("2. PortfolioManager的record_equity_history方法未被调用")
                    st.write("3. 净值数据格式转换失败")
                    
                    # 显示回测结果结构信息
                    if results:
                        st.write("回测结果包含的键:", list(results.keys()))
                        if "equity_records" in results:
                            st.write("equity_records类型:", type(results["equity_records"]))
                            if hasattr(results["equity_records"], '__len__'):
                                st.write("equity_records长度:", len(results["equity_records"]))
            
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
                        
                        elif strategy_config['type'] == 'martingale':
                            initial_ratio = params.get('initial_ratio', 0.1) * 100
                            multiplier = params.get('multiplier', 2.0)
                            clear_on_insufficient = params.get('clear_on_insufficient', True)
                            
                            st.metric("初始开仓比例", f"{initial_ratio:.2f}%")
                            st.metric("加仓倍数", f"{multiplier:.1f}")
                            st.metric("资金不足清仓", "是" if clear_on_insufficient else "否")
                    
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
                        elif strategy_config['type'] == 'martingale':
                            st.info("""
                            **马丁策略 (Martingale)**
                            - 初始开仓使用固定比例资金
                            - 每次加仓金额按倍数递增: $x * k^n$
                            - 资金不足时自动触发清仓
                            - 适合震荡行情和网格交易
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
                            
                            # 获取初始资金（从回测配置或结果中）
                            initial_capital = backtest_config.initial_capital
                            if "summary" in results:
                                initial_capital = results["summary"].get('initial_capital', backtest_config.initial_capital)
                            
                            avg_position_pct = (avg_trade_amount / initial_capital) * 100
                            
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("平均单笔交易金额", f"¥{avg_trade_amount:,.0f}")
                            with col2:
                                st.metric("平均仓位占比", f"{avg_position_pct:.2f}%")
                            with col3:
                                # 计算仓位利用率
                                max_position_value = equity_data['total_value'].max() if 'total_value' in equity_data.columns else 0
                                position_utilization = (max_position_value / initial_capital) * 100
                                st.metric("最大仓位利用率", f"{position_utilization:.2f}%")
                else:
                    st.info("暂无仓位策略配置信息")

            with tab8:
                # 显示策略配置信息
                st.subheader("📊 策略配置信息")

                # 显示默认策略配置
                st.write("**默认策略配置**")
                if 'default_strategy' in results:
                    default_strategy = results['default_strategy']
                    st.json(default_strategy)
                else:
                    st.info("无默认策略配置信息")

                # 显示策略映射
                st.write("**各股票策略配置**")
                if 'strategy_mapping' in results and results['strategy_mapping']:
                    for symbol, strategy_config in results['strategy_mapping'].items():
                        st.write(f"**{symbol}**")
                        st.json(strategy_config)
                else:
                    st.info("无策略映射配置信息")

        else:
            st.error("回测失败，请检查输入参数")
