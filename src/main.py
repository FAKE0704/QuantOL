
from core.data import *
from core.data.database import DatabaseManager
from core.data.baostock_source import BaostockDataSource
import asyncio
from core.strategy import *
from core.execution import *
from core.risk import *
from frontend.visualization import *
# from backend.api import *
from support import *
import seaborn as sns
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from ipywidgets import interact
import openpyxl
import matplotlib.pyplot as plt
# from st_aggrid import AgGrid, GridOptionsBuilder


# 获取多个年份的节假日
# years = range(2004, 2025)  # 需要覆盖的年份
# holidays = []
# for year in years:
#     holidays.extend(get_china_holidays(year))
# holidays = [holiday.strftime("%Y-%m-%d") for holiday in holidays]


### 测试 #####


# 初始化数据库
db_manager = DatabaseManager()
db_manager.init_db()
st.title("股票数据测试")
async def test():
    # 从数据库获取数据
    df =await db_manager.load_stock_data("sh.600622", "20250101", "20250307", frequency = "5")
    print(df.head(2))
asyncio.run(test())

# st.write(df)






















# 股票日期设置
col1, col2, col3 = st.columns(3)
# 在第一个列中放置第一个选择框
with col1:
    start_year = st.selectbox("选择开始年份", range(2000, 2030), index=20)

with col2:
    start_month = st.selectbox("选择开始月份", range(1, 13), index=10)

col1, col2 = st.columns(2)
with col1:
    end_year = st.selectbox("选择结束年份", range(start_year, 2030), index=1)

with col2:
    end_month = st.selectbox("选择结束月份", range(1, 13), index=0)

start_time = f"{start_year}-{start_month}"

end_time = f"{end_year}-{end_month}"

# data.set_time_interval(start_time,end_time)

# st.write(data.data.head(2))




# ======================作图======================
# 设置参数
st.title("Choose Your Parameters")
# (
#     max_window,
#     RSI_parameter,
#     short_window,
#     long_window,
#     signal_window,
#     profit_threshold,
#     MA_drawdown_low,
#     rsi_36_low,
#     rsi_240_low,
# ) = set_factor()

# MACD_parameter = [
#     short_window,
#     signal_window,
#     long_window
# ]
# 指标计算
# data.get_sma(max_window) # 应该不需要全部window的
# data.get_macd(short_window, signal_window,long_window)
# data.get_rsi(RSI_parameter)


    # precompute_profit_opportunities

#     # 指标计算
#     ma_dict, data = precompute_SMA(data, max_window)
#     macd_dict, data = precompute_MACD(data, short_window, long_window, signal_window)
#     RSI_dict, data = precompute_RSI(data, RSI_parameter)
#     opportunities = precompute_profit_opportunities(
#         data, price_col="close", time_col="time", profit_threshold=profit_threshold
#     )

#     ma_window = st.selectbox("选择MA作图窗口", range(1, max_window + 1), index=47)

#     data[f"SMA_{ma_window}_pct"] = (
#         data[f"SMA_{ma_window}"].pct_change() * 10000
#     )  # 48MA变化率 * 10000
#     st.write(data.head(50))



#     # # ==============第一个什么图？=============
#     # # 选择MA作图窗口
#     # fig2 = go.Figure()
#     # fig2.add_trace(
#     #     go.Scatter(
#     #         # x=data["time"],
#     #         x=stock_data.index,
#     #         y=stock_data["close"],
#     #         yaxis="y1",
#     #         mode="lines",
#     #         line=dict(width=0.8),
#     #         name="close",
#     #         hovertext=data["time"],
#     #     )
#     # )
#     # fig2.update_layout(
#     #     title="Close",
#     #     xaxis=dict(
#     #         title="时间",
#     #         tickvals=stock_data.index[::1000],  # 用于定位的值
#     #         ticktext=stock_data["time"][::1000],  # 想要显示在 x 轴上的值
#     #         tickangle=45,  # 如果时间标签很长，可以旋转以便阅读
#     #     ),
#     #     yaxis=dict(
#     #         title="Close Price",  # 左侧 y 轴标题
#     #         titlefont=dict(color="blue"),  # 左侧 y 轴字体颜色
#     #         tickfont=dict(color="blue"),  # 左侧 y 轴刻度颜色
#     #     ),
#     #     template="plotly",
#     #     legend=dict(x=0.5, y=1.1),  # 设置图例位置
#     #     hovermode="x unified",
#     # )

#     # st.plotly_chart(fig2)


# fig1.drawRSI(RSI_parameter,"white")
# fig1.drawClose("blue")
# fig1.draw()
# fig2 = Drawer(data)
# fig2.drawClose("red")
# fig2.drawRSI(12,"white")
# fig2.drawRSI(120,"white")
# fig2.draw()

# 信号设置

col1, col2 = st.columns(2)
# 在第一个列中放置第一个选择框
with col1:
    ma_para_1 = st.selectbox("选择均线参数1", range(1, 52), index=1)

with col2:
    ma_para_2 = st.selectbox("选择均线参数2", range(1, 52), index=1)



col1, col2 ,col3= st.columns(3)
with col1:
    rsi_para_window = st.selectbox("选择RSI_b参数:window", range(0, 52), index=12)

with col2:
    rsi_para_b = st.selectbox("选择RSI_b参数:阈值", range(0, 52), index=30)

with col3:
    rsi_para_s = st.selectbox("选择RSI_s参数:阈值", range(49, 100), index=20)

st.write("均线参数1<均线参数2")


if st.button('执行回测'):
    # 按钮被点击后执行的代码
    data = Data(stock,"5") # 考虑多变量

    szzhzs_d = Data("上证综合指数","d")

    # s1b1 = True
    s1b1 = (data.get_sma(int(ma_para_1))>data.get_sma(int(ma_para_2))) # MA short >MA long
    # s1b1 = (data.get_sma(ma_para_1)>data.get_sma(ma_para_2))&(data.get_sma(ma_para_2)>data.get_sma(20))&(data.get_sma(20)>data.get_sma(60))
    # s1b2 = data.get_sma(ma_para_1)>data.get_sma(ma_para_2).shift(1)
    s1b2 =   ((data.get_rsi(int(rsi_para_window)) < int(rsi_para_b)).shift(1)<int(rsi_para_b)) & (data.get_rsi(int(rsi_para_window)) >= int(rsi_para_b)) # RSI ↑ buy index
    s1b3 = True
    # s1b3 = data.get_macd(36,54,72) < 0

    s1s1 = True
    # s1s1 = (data.get_sma(int(ma_para_1))<data.get_sma(int(ma_para_2)))
    # s1s1 = (data.get_sma(ma_para_1)<data.get_sma(ma_para_2))&(data.get_sma(ma_para_2)<data.get_sma(20))&(data.get_sma(20)<data.get_sma(60))
    s1s2 = data.get_rsi(int(rsi_para_window)) > int(rsi_para_s)

    strategy1 = Strategy(Data = data,name = "均线排列策略",buySignal = s1b1&s1b2&s1b3, sellSignal = s1s1&s1s2)
    strategy1.get_strategy()
    bt1 = BackTesting(strategy1)

    st.title("Debug") # Strategy data没问题

    st.write(bt1.Strategy.Data.data) # bt1 data debug
    # st.write(bt1.buyTrade) # bt1 data debug
    # st.write(bt1.profit_cum.shape[0]) # self.Strategy.Data.data正常
    # st.write(bt1.buyTrade) # buyTrade有信息
    bt1.get_data()

    # fig3 = Drawer(bt1)
    # fig3.drawClose("red")
    # fig3.drawMA(5,"green")
    # fig3.drawMA(10,"blue")
    # fig3.draw()

    st.write("BSpoint")
    BS = Drawer(bt1)
    BS.drawBS()
    BS.draw()   

    MA = Drawer(bt1)
    MA.drawMA(5,"yellow")
    MA.drawMA(15,"blue")
    MA.drawMA(60,"white")
    MA.draw()


#     fig = go.Figure()
#     # =============================绘制 Close=============================
#     fig.add_trace(
#         go.Scatter(
#             # x=data["time"],
#             x=data.index,
#             y=data["close"],
#             yaxis="y1",
#             mode="lines",
#             line=dict(width=0.8),
#             showlegend=False,
#             name="close",
#             hovertext=data["time"],
#         )
#     )

#     # RSI Hover
#     fig.add_trace(
#         go.Scatter(
#             # x=data["time"],
#             x=data.index,
#             y=2 + data["12RSI"] * 0.01,
#             yaxis="y1",
#             mode="lines",
#             line=dict(width=0.06),
#             showlegend=False,
#             hovertext=data["12RSI"].apply(lambda x: f"12RSI: {x}"),
#             hoverinfo="text",
#         )
#     )

#     # RSI Hover
#     fig.add_trace(
#         go.Scatter(
#             # x=data["time"],
#             x=data.index,
#             y=2 + data["36RSI"] * 0.01,
#             yaxis="y1",
#             mode="lines",
#             line=dict(width=0.06),
#             showlegend=False,
#             hovertext=data["36RSI"].apply(lambda x: f"36RSI: {x}"),
#             hoverinfo="text",
#         )
#     )

#     # RSI Hover
#     fig.add_trace(
#         go.Scatter(
#             # x=data["time"],
#             x=data.index,
#             y=2 + data["48RSI"] * 0.01,
#             yaxis="y1",
#             mode="lines",
#             line=dict(width=0.06),
#             showlegend=False,
#             hovertext=data["48RSI"].apply(lambda x: f"48RSI: {x}"),
#             hoverinfo="text",
#         )
#     )

#     # RSI Hover
#     fig.add_trace(
#         go.Scatter(
#             # x=data["time"],
#             x=data.index,
#             y=2 + data["96RSI"] * 0.01,
#             yaxis="y1",
#             mode="lines",
#             line=dict(width=0.06),
#             showlegend=False,
#             hovertext=data["96RSI"].apply(lambda x: f"96RSI: {x}"),
#             hoverinfo="text",
#         )
#     )

#     # RSI Hover
#     fig.add_trace(
#         go.Scatter(
#             # x=data["time"],
#             x=data.index,
#             y=2 + data["720RSI"] * 0.01,
#             yaxis="y1",
#             mode="lines",
#             line=dict(width=0.06),
#             showlegend=False,
#             hovertext=data["720RSI"].apply(lambda x: f"720RSI: {x}"),
#             hoverinfo="text",
#         )
#     )

#     # MACD Hover 
#     fig.add_trace(
#         go.Scatter(
#             # x=data["time"],
#             x=data.index,
#             y=3 + data["MACD"],
#             yaxis="y1",
#             mode="lines",
#             line=dict(width=0.5, color="white"),
#             showlegend=False,
#             hovertext=data["MACD"].apply(lambda x: f"MACD: {x}"),
#             hoverinfo="text",
#         )
#     )

#     # Hover: pct of 720RSI
#     data["720RSI_5shift_ratio"] = data["720RSI"].shift(5) / data["720RSI"]
#     fig.add_trace(
#         go.Scatter(
#             # x=data["time"],
#             x=data.index,
#             y=data["720RSI_5shift_ratio"],
#             yaxis="y1",
#             mode="lines",
#             line=dict(width=0.5, color="white"),
#             showlegend=False,
#             hovertext=data["720RSI_5shift_ratio"].apply(lambda x: f"720RSI Ratio: {x:.2f}"),
#             hoverinfo="text",
#         )
#     )

#     # =============================绘制 MA=============================
#     fig.add_trace(
#         go.Scatter(
#             # x=data["time"],
#             x=data.index,
#             y=ma_dict[ma_window],
#             yaxis="y1",
#             mode="lines",
#             line=dict(width=0.8),
#             name=f"MA({ma_window})",
#             hovertext=data[f"SMA_{ma_window}_pct"].apply(lambda x: f"{x:.4f}%"),
#             hoverinfo="y+text",
#         )
#     )
#     # 绘制 Volume
#     fig.add_trace(
#         go.Bar(  # x=data["time"],
#             x=data.index, y=data["volume"], yaxis="y2", name=f"volume"
#         )
#     )

#     opportunities = pd.DataFrame(
#         opportunities, columns=["low_idx", "low_price", "high_idx", "high_price"]
#     )
#     # ======================绘制 盈利箭头=================================
#     st.write("opportunities")
#     st.write(opportunities)
#     for index, row in opportunities.iterrows():
#         fig.add_trace(
#             go.Scatter(
#                 x=[row["low_idx"], row["high_idx"]],
#                 y=[row["low_price"], row["high_price"]],
#                 yaxis="y1",
#                 mode="markers+lines",
#                 line=dict(color="yellow", dash="dot", width=0.9),
#                 marker=dict(size=4, symbol="arrow-bar-up"),
#                 showlegend=False,
#                 name=f"Opportunity {index+1}",  #
#             )
#         )

#     # 历史好机会feature
#     feature = data[data.index.isin(opportunities["low_idx"])]
#     # feature.insert(0, "序号", range(1, len(feature) + 1))
#     st.write("feature")
#     st.write(feature)

#     # 通用买点
#     consider_buy = data[
#         (data["12RSI"] < feature["12RSI"].quantile(0.75) - 5)  # RSI
#         & (data["12RSI"] > feature["12RSI"].quantile(0.25))  # RSI
#         # &(data['close'].shift(1).diff()/data['close'].shift(1)>0) # 价格上涨 # 有问题
#         & (data["Close-SMA_240(%)"] < feature["Close-SMA_240(%)"].quantile(0.75))
#         & (data["Close-SMA_240(%)"] > feature["Close-SMA_240(%)"].quantile(0.25))
#         & (data["MACD"] < feature["MACD"].quantile(0.75))  # MACD
#         & (data["MACD"] > feature["MACD"].quantile(0.25))  # MACD
#         & (data["DIF"] < feature["DIF"].quantile(0.75))
#         # &(data['DIF'].diff()>0)
#     ]  # macd图开始上升,dif dea

#     # ==========================Strategy=================================
#     buy_strategy_1 = data[
#         # 买入：48RSI从下往上穿30 --
#         ## row 1: RSI < 30 , row 2: RSI >= 30 , row 2 <-- buy signal
#         ((data["720RSI"]<50)&((data["12RSI"].shift(1) < 30) & (data["12RSI"] >= 30)))
#         |((data["720RSI"]>=50)&((data["12RSI"].shift(1) < 40) & (data["12RSI"] >= 40)))  # 48RSI从下往上穿35
#         & (data["MACD"] < 0)
#         #& (data["12RSI"] <= 30)
#         # & (data[f"SMA_{ma_window}_pct"] > -8)
#         & (data["720RSI"].shift(5)/data["720RSI"] < 1)  # 720RSI上扬？
#         # & ((data["720RSI"].isna())|(data["720RSI"] <= 50))
        
        
#         # ---------------back up----------------
#         # ((data["12RSI"] < 20) |(data["12RSI"].shift(1) < 20) | (data["12RSI"].shift(2) < 20))
        
        
#         # & (data[f'SMA_{ma_window}_pct'] > -MA_drawdown_low)  # 近10天均值
#         # & (data[f'SMA_{ma_window}_pct'] < -2)
#         # & ((data["36RSI"] < rsi_36_low) |(data["36RSI"].shift(1) < rsi_36_low) | (data["36RSI"].shift(2) < rsi_36_low))
#         # & (data["MACD"] < 0)  # MACD小于0
#         # 上涨趋势&rsi下限高;下跌趋势&rsi下限低;
#         # & (((data[f"SMA_{ma_window}_pct"] > 0) & (data["240RSI"] < rsi_240_low))| ((data[f"SMA_{ma_window}_pct"] <= 0) & (data["240RSI"] < rsi_240_low - 10)))
#         # & (data["95RSI"] < 35)
#         # & (data["MACD"] > feature["MACD"].quantile(0.25))  # MACD
#     ].index

#     sell_strategy_1 = data[
#         # 卖出：RSI从上往下穿70 --
#         ## row 1: RSI > 70 , row 2: RSI <= 70 , row 2 <-- buy signal
#         (data["48RSI"].shift(1) > 70)  # 上一行大于70
#         & (data["48RSI"] <= 70)  # 当前行<=70
#         # 增长率>万8
#         & (data[f"SMA_{ma_window}_pct"] > 3)
#         & (data["MACD"] > 0)  # MACD
#     ].index

    
#     # 买卖信号
#     data.loc[buy_strategy_1, "Buy_Signal"] = 1
#     data.loc[sell_strategy_1, "Sell_Signal"] = 1
    
#     data.loc[data.index.difference(buy_strategy_1), "Buy_Signal"] = 0
#     data.loc[data.index.difference(sell_strategy_1), "Sell_Signal"] = 0
#     # 买卖量
#     balance = 100 * 10000  #   起始金额100w
#     data = PositionSizing(data, balance)
#     # ================收益率作图===================
#     profit_cal(data)
#     st.title("data-被迫平仓")
#     st.write(data[data['ForcedTrade']==1])

#     # strategy_1:RSI规律，买点信号白，卖点信号黄
#     strategies = [buy_strategy_1, sell_strategy_1]
#     colors = ["white", "red"]
#     # =================画strategy买卖点==============
#     for strategy, color in zip(strategies, colors):
#         fig.add_trace(
#             go.Scatter(
#                 # x=consider_buy["time"],
#                 x=strategy,
#                 marker=dict(size=6),
#                 y=data.loc[strategy.tolist(), "close"],
#                 yaxis="y1",
#                 mode="markers",
#                 name=f"strategy_1",
#                 marker_color=color,
#             )
#         )

#     # ====================实际买卖点位===========
#     actual_buy = data[data["BuyTrade"] != 0]
#     actual_sell = data[data["SellTrade"] != 0]
#     st.title("Actual Buy")
#     st.write(actual_buy)
#     st.title("Actual Sell")
#     st.write(actual_sell)

#     actual_buyNsell = [
#         data[data["BuyTrade"] != 0].index.tolist(),
#         data[data["SellTrade"] != 0].index.tolist(),
#     ]
#     actual_buyNsell_price = [
#         data.loc[data["BuyTrade"] != 0, "close"],
#         data.loc[data["SellTrade"] != 0, "close"],
#     ]
#     colors = ["white", "red"] # 1-buy 2-sell
#     # =================strategy买卖点==============
#     for bNs, bNs_price, color in zip(
#         actual_buyNsell, actual_buyNsell_price, colors
#     ):
#         fig.add_trace(
#             go.Scatter(
#                 # x=consider_buy["time"],
#                 x=bNs,
#                 y=bNs_price + 0.2,
#                 yaxis="y1",
#                 mode="markers",
#                 name="bNs",
#                 marker=dict(color=color, size=9, symbol="triangle-down"),
#             )
#         )

#     # 更新布局
#     fig.update_layout(
#         title="Close and MA",
#         xaxis=dict(
#             title="时间",
#             tickvals=data.index[::1000],  # 用于定位的值
#             ticktext=data["time"][::1000],  # 想要显示在 x 轴上的值
#             tickangle=45,  # 如果时间标签很长，可以旋转以便阅读
#             # rangebreaks=[
#             #     dict(bounds=[6, 1], pattern="day of week"),  # 排除周末
#             #     dict(values=holidays),  # 排除法定节假日
#             #     dict(bounds=[11.51, 13.01], pattern="hour"),  # 排除中午非交易时间
#             #     dict(bounds=[15.01, 23], pattern="hour"),  # 排除下午非交易时间
#             #     dict(bounds=[0, 9.49], pattern="hour"),  # 排除下午非交易时间
#             # ],  # 排除非营业时间（交易时间为9:30-11:30，13:00-15:00）
#         ),
#         yaxis=dict(
#             title="Close Price",  # 左侧 y 轴标题
#             titlefont=dict(color="blue"),  # 左侧 y 轴字体颜色
#             tickfont=dict(color="blue"),  # 左侧 y 轴刻度颜色
#         ),
#         yaxis2=dict(
#             title="volume",  # 右侧 y 轴标题
#             titlefont=dict(color="orange"),  # 右侧 y 轴字体颜色
#             tickfont=dict(color="orange"),  # 右侧 y 轴刻度颜色
#             overlaying="y",  # 将右侧 y 轴叠加在左侧 y 轴
#             side="right",  # 将右侧 y 轴显示在右边
#             range=[0, data["volume"].max() * 4],  # 设置右侧 y 轴的显示范围
#         ),
#         template="plotly",
#         legend=dict(x=0.1, y=1.1),  # 设置图例位置
#         hovermode="x unified",
#         bargap=0.3,  # 调整柱状图之间的间距
#     )

#     st.title("Those are the good points")
#     st.dataframe(feature, height=100)
#     st.title("Maybe the good buy points")

#     st.dataframe(consider_buy, height=100)
#     st.title("股票图像")
#     st.plotly_chart(fig)

#     #=====Research RSI======
#     RSI_window_1 = st.selectbox(
#         "请选择RSI参数1",
#         [12, 24, 48, 96, 240, 360, 720, 1440],
#         index=2,
#         key="rsi_selectbox_1",
#     )
#     # 初始化session_state中的变量
#     if "rsi_window_1" not in st.session_state:
#         st.session_state.rsi_window_1 = 48  # 默认值
#         drawallRSI(data, 48, "white", 1)
    
    
#     RSI_window_2 = st.selectbox(
#         "请选择RSI参数2",
#         [12, 24, 48, 96, 240, 300,360,540, 720, 1440],
#         index=2,
#         key="rsi_selectbox_2",
#     )
#     # 初始化session_state中的变量
#     if "rsi_window_2" not in st.session_state:
#         st.session_state.rsi_window_2 = 720  # 默认值
#         drawallRSI(data, 720, "white", 1)
    
#     # 检查用户是否更改了选择
#     if (RSI_window_1 != st.session_state.rsi_window_1)|(RSI_window_2 != st.session_state.rsi_window_2):
#         st.session_state.rsi_window_1 = RSI_window_1  # 更新session_state中的值
#         drawallRSI(data, RSI_window_1, "white", 1)  # 重新作图RSI

#         st.session_state.rsi_window_2 = RSI_window_2  # 更新session_state中的值
#         drawallRSI(data, RSI_window_2, "white", 1)  # 重新作图RSI
    
#     # 画rsi的boll

#     st.text(
#         f"""
#         买点{len(buy_strategy_1.tolist())}个
#         卖点{len(sell_strategy_1.tolist())}个
#         """
#     )

#     # st.plotly_chart(fig3, use_container_width=True)

#     st.title("Today Factors")
#     st.write(data.iloc[-1:])

#     # ————————seaborn————————
#     # 将数据转换为长格式
#     st.title("Data Distribution")
#     feature_long = pd.melt(
#         feature,
#         value_vars=["12RSI","36RSI","48RSI","240RSI", "MACD", "Close-SMA_240(%)", "DIF", "volume"],
#         var_name="Metric",
#         value_name="Value",
#     )
#     if feature_long.empty:
#         print("数据框为空，请检查数据加载和处理步骤。")
#     else:
#         g = sns.FacetGrid(
#             feature_long,
#             col="Metric",
#             col_wrap=4,
#             height=1,
#             sharex=False,
#             sharey=False,
#         )
#         g.figure.set_size_inches(10, 5)  # 设置图表布局：10：5
#         # 为每个子集绘制箱线图
#         g.map(sns.boxplot, "Value")

#         # 添加标题
#         g.set_titles(col_template="{col_name}")

#         # 显示图表
#         st.pyplot(g)

#     # drawRSI(data, 'close', 'white', 'RSI', 'red', 0.5)

#     # 好买点参数

#     st.text(
#         f"""
#         使用的参数为:RSI:{feature['12RSI'].quantile(0.75)-5:.1f}~{feature['12RSI'].quantile(0.25):.1f}
#         Close-SMA_240(%):{feature['Close-SMA_240(%)'].quantile(0.75):.1f}~{feature['Close-SMA_240(%)'].quantile(0.25):.1f}
#         MACD:{feature['MACD'].quantile(0.75):.1f}~{feature['MACD'].quantile(0.25):.1f}
#         DIF:{feature['DIF'].quantile(0.75):.1f}~{feature['DIF'].quantile(0.25):.1f}
#         """
#     )

#     # 显示数据表
#     st.subheader("Data Set")
#     st.write(data.head(2))
#     st.write(data[["time", "close", "volume"]])
