"""
DS API:sk-57e9b22fe11e432286f98b5fbcdbbbab

# 
git clone https://github.com/FAKE0704/VSC_work.git
git add .
git commit -m "提交"
git push origin main


# Mac
source venv/bin/activate


# Win
.\.venv\Scripts\activate
.\Djangovenv\Scripts\activate


# run streamlit 
在vsc_work路径下：
streamlit run src/Data_Visualization/main.py 


"""

from profitNrisk import *

from src.strategy.factor_precompute import *
from src.data.database import *
import seaborn as sns
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from ipywidgets import interact
import openpyxl
import matplotlib.pyplot as plt
from st_aggrid import AgGrid, GridOptionsBuilder


# # 数据库
# import mysql.connector
# # 连接到 MySQL 数据库
# db = mysql.connector.connect(
#     host="localhost",  # 数据库主机地址
#     user="your_username",  # 数据库用户名
#     password="your_password",  # 数据库密码
#     database="your_database"  # 数据库名
# )

# # 创建一个游标对象，用于执行 SQL 语句
# cursor = db.cursor()

# # 创建表的 SQL 语句
# create_table_query = """
# CREATE TABLE IF NOT EXISTS users (
#     id INT AUTO_INCREMENT PRIMARY KEY,
#     name VARCHAR(255) NOT NULL,
#     email VARCHAR(255)
# );
# """

# # 执行创建表的 SQL 语句
# cursor.execute(create_table_query)

# # 插入数据的 SQL 语句
# insert_data_query = """
# INSERT INTO users (name, email) VALUES (%s, %s)
# """

# # 要插入的数据
# users = [
#     ('Alice', 'alice@example.com'),
#     ('Bob', 'bob@example.com'),
#     ('Charlie', 'charlie@example.com')
# ]

# # 执行插入数据的 SQL 语句
# cursor.executemany(insert_data_query, users)

# # 提交事务
# db.commit()

# # 查询数据的 SQL 语句
# select_data_query = "SELECT * FROM users"

# # 执行查询数据的 SQL 语句
# cursor.execute(select_data_query)

# # 获取查询结果
# users_data = cursor.fetchall()

# # 打印查询结果
# for user in users_data:
#     print(user)


# # 关闭游标和数据库连接
# cursor.close()
# db.close()
def drawallRSI(data, window, color, line_width):
    """
    color:线的颜色
    line_width:width,线的粗细
    """
    fig_rsi = go.Figure()
    fig_rsi.add_trace(
        # 绘制RSI
        go.Scatter(
            x=data.index,
            y=data[f"{window}RSI"],
            yaxis="y1",
            mode="lines",
            line=dict(color=color, width=line_width),
            name=f"{window}RSI",
            hovertext=data["time"],
        )
    )
    fig_rsi.update_layout(
        title=f"{window}RSI",
        xaxis=dict(
            title="时间",
            tickvals=data.index[::1000],
            ticktext=data["time"][::1000],
            # tickangle=45,
        ),
        yaxis=dict(
            title=f"{window}RSI",
            titlefont=dict(color="white"),
            tickfont=dict(color="white"),
            tickvals=[30, 70],
            ticktext=["30", "70"],
        ),
        template="plotly",
        legend=dict(x=0.5, y=1.1),
        hovermode="x unified",
    )

    st.plotly_chart(fig_rsi)


def drawRSI(data, feature1, line1_col, RSI, line2_col, line_width):
    """
    feature1 2:column,需要绘制的特征
    line_col:color,线的颜色
    line_width:width,线的粗细
    """
    fig4 = go.Figure()
    fig4.add_trace(
        # 添加RSI大于70或小于30的数据点，设置为白色线
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

    # 添加RSI大于70或小于30的数据点，设置为白色线
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

    # 添加RSI小于70且大于30的数据点，设置为第二种颜色线
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
            # range=[0, data["volume"].max() * 4],
        ),
        template="plotly",
        legend=dict(x=0.5, y=1.1),
        hovermode="x unified",
    )

    st.title("股票图像")
    st.plotly_chart(fig4)


# 获取多个年份的节假日
years = range(2004, 2025)  # 需要覆盖的年份
holidays = []
for year in years:
    holidays.extend(get_china_holidays(year))

holidays = [holiday.strftime("%Y-%m-%d") for holiday in holidays]

# ========数据加载========
st.title("Choose Your Stock")
if st.button("更新数据"):
    update_data_now()
    st.write("更新成功！")


uploaded_file = st.selectbox(
    "请选择文件进行上传", ["光大嘉宝", "天风证券", "中油资本", "上证综合指数"]
)
uploaded_file = f"{uploaded_file}最新数据.xlsx"

st.write(f"当前工作路径：{os.getcwd()}")

data = load_data(uploaded_file)
# test data

stock_data = load_data("上证综合指数最新数据.xlsx")


st.write(stock_data.shape)

# 股票日期设置
col1, col2, col3 = st.columns(3)
# 在第一个列中放置第一个选择框
with col1:
    start_year = st.selectbox("选择开始年份", range(2000, 2030), index=20)

with col2:
    start_month = st.selectbox("选择开始月份", range(1, 13), index=0)

col1, col2 = st.columns(2)
with col1:
    end_year = st.selectbox("选择结束年份", range(start_year, 2030), index=1)

with col2:
    end_month = st.selectbox("选择结束月份", range(1, 13), index=0)
data = data[
    (
        (data["time"].dt.year > start_year)
        | (data["time"].dt.year == start_year) & (data["time"].dt.month > start_month)
    )
    & (
        (data["time"].dt.year < end_year)
        | (data["time"].dt.year == end_year) & (data["time"].dt.month < end_month)
    )
]
data = data.reset_index(drop=True)

st.write(data.head(2))

# ======================作图======================
if "time" in data.columns and "close" in data.columns:
    # 设置参数
    st.title("Choose Your Parameters")
    (
        max_window,
        RSI_parameter,
        short_window,
        long_window,
        signal_window,
        profit_threshold,
        MA_drawdown_low,
        rsi_36_low,
        rsi_240_low,
    ) = set_factor()

    # 指标计算
    ma_dict, data = precompute_SMA(data, max_window)
    macd_dict, data = precompute_MACD(data, short_window, long_window, signal_window)
    RSI_dict, data = precompute_RSI(data, RSI_parameter)
    opportunities = precompute_profit_opportunities(
        data, price_col="close", time_col="time", profit_threshold=profit_threshold
    )

    ma_window = st.selectbox("选择MA作图窗口", range(1, max_window + 1), index=47)

    data[f"SMA_{ma_window}_pct"] = (
        data[f"SMA_{ma_window}"].pct_change() * 10000
    )  # 48MA变化率 * 10000
    st.write(data.head(50))
    if st.button("生成图像"):

        # ==============第一个图=============
        # 选择MA作图窗口
        fig2 = go.Figure()
        fig2.add_trace(
            go.Scatter(
                # x=data["time"],
                x=stock_data.index,
                y=stock_data["close"],
                yaxis="y1",
                mode="lines",
                line=dict(width=0.8),
                name="close",
                hovertext=data["time"],
            )
        )
        fig2.update_layout(
            title="Close",
            xaxis=dict(
                title="时间",
                tickvals=stock_data.index[::1000],  # 用于定位的值
                ticktext=stock_data["time"][::1000],  # 想要显示在 x 轴上的值
                tickangle=45,  # 如果时间标签很长，可以旋转以便阅读
            ),
            yaxis=dict(
                title="Close Price",  # 左侧 y 轴标题
                titlefont=dict(color="blue"),  # 左侧 y 轴字体颜色
                tickfont=dict(color="blue"),  # 左侧 y 轴刻度颜色
            ),
            template="plotly",
            legend=dict(x=0.5, y=1.1),  # 设置图例位置
            hovermode="x unified",
        )

        st.plotly_chart(fig2)

        fig = go.Figure()
        # =============================绘制 Close=============================
        fig.add_trace(
            go.Scatter(
                # x=data["time"],
                x=data.index,
                y=data["close"],
                yaxis="y1",
                mode="lines",
                line=dict(width=0.8),
                showlegend=False,
                name="close",
                hovertext=data["time"],
            )
        )

        # RSI Hover
        fig.add_trace(
            go.Scatter(
                # x=data["time"],
                x=data.index,
                y=2 + data["12RSI"] * 0.01,
                yaxis="y1",
                mode="lines",
                line=dict(width=0.06),
                showlegend=False,
                hovertext=data["12RSI"].apply(lambda x: f"12RSI: {x}"),
                hoverinfo="text",
            )
        )

        # RSI Hover
        fig.add_trace(
            go.Scatter(
                # x=data["time"],
                x=data.index,
                y=2 + data["36RSI"] * 0.01,
                yaxis="y1",
                mode="lines",
                line=dict(width=0.06),
                showlegend=False,
                hovertext=data["36RSI"].apply(lambda x: f"36RSI: {x}"),
                hoverinfo="text",
            )
        )

        # RSI Hover
        fig.add_trace(
            go.Scatter(
                # x=data["time"],
                x=data.index,
                y=2 + data["48RSI"] * 0.01,
                yaxis="y1",
                mode="lines",
                line=dict(width=0.06),
                showlegend=False,
                hovertext=data["48RSI"].apply(lambda x: f"48RSI: {x}"),
                hoverinfo="text",
            )
        )

        # RSI Hover
        fig.add_trace(
            go.Scatter(
                # x=data["time"],
                x=data.index,
                y=2 + data["96RSI"] * 0.01,
                yaxis="y1",
                mode="lines",
                line=dict(width=0.06),
                showlegend=False,
                hovertext=data["96RSI"].apply(lambda x: f"96RSI: {x}"),
                hoverinfo="text",
            )
        )

        # RSI Hover
        fig.add_trace(
            go.Scatter(
                # x=data["time"],
                x=data.index,
                y=2 + data["240RSI"] * 0.01,
                yaxis="y1",
                mode="lines",
                line=dict(width=0.06),
                showlegend=False,
                hovertext=data["240RSI"].apply(lambda x: f"240RSI: {x}"),
                hoverinfo="text",
            )
        )

        # MACD Hover
        fig.add_trace(
            go.Scatter(
                # x=data["time"],
                x=data.index,
                y=3 + data["MACD"],
                yaxis="y1",
                mode="lines",
                line=dict(width=0.5, color="white"),
                showlegend=False,
                hovertext=data["MACD"].apply(lambda x: f"MACD: {x}"),
                hoverinfo="text",
            )
        )

        # =============================绘制 MA=============================
        fig.add_trace(
            go.Scatter(
                # x=data["time"],
                x=data.index,
                y=ma_dict[ma_window],
                yaxis="y1",
                mode="lines",
                line=dict(width=0.8),
                name=f"MA({ma_window})",
                hovertext=data[f"SMA_{ma_window}_pct"].apply(lambda x: f"{x:.4f}%"),
                hoverinfo="y+text",
            )
        )
        # 绘制 Volume
        fig.add_trace(
            go.Bar(  # x=data["time"],
                x=data.index, y=data["volume"], yaxis="y2", name=f"volume"
            )
        )

        opportunities = pd.DataFrame(
            opportunities, columns=["low_idx", "low_price", "high_idx", "high_price"]
        )
        # 绘制 盈利箭头：从 lowpoint 到 highpoint
        st.write("opportunities")
        st.write(opportunities)
        for index, row in opportunities.iterrows():
            fig.add_trace(
                go.Scatter(
                    x=[row["low_idx"], row["high_idx"]],
                    y=[row["low_price"], row["high_price"]],
                    yaxis="y1",
                    mode="markers+lines",
                    line=dict(color="yellow", dash="dot", width=0.9),
                    marker=dict(size=4, symbol="arrow-bar-up"),
                    showlegend=False,
                    name=f"Opportunity {index+1}",  #
                )
            )

        # 历史好机会feature
        feature = data[data.index.isin(opportunities["low_idx"])]
        # feature.insert(0, "序号", range(1, len(feature) + 1))
        st.write("feature")
        st.write(feature)

        # 通用买点
        consider_buy = data[
            (data["12RSI"] < feature["12RSI"].quantile(0.75) - 5)  # RSI
            & (data["12RSI"] > feature["12RSI"].quantile(0.25))  # RSI
            # &(data['close'].shift(1).diff()/data['close'].shift(1)>0) # 价格上涨 # 有问题
            & (data["Close-SMA_240(%)"] < feature["Close-SMA_240(%)"].quantile(0.75))
            & (data["Close-SMA_240(%)"] > feature["Close-SMA_240(%)"].quantile(0.25))
            & (data["MACD"] < feature["MACD"].quantile(0.75))  # MACD
            & (data["MACD"] > feature["MACD"].quantile(0.25))  # MACD
            & (data["DIF"] < feature["DIF"].quantile(0.75))
            # &(data['DIF'].diff()>0)
        ]  # macd图开始上升,dif dea

        # ==========================Strategy=================================
        buy_strategy_1 = data[
            # 买入：48RSI从下往上穿30 --
            ## row 1: RSI < 30 , row 2: RSI >= 30 , row 2 <-- buy signal
            
            (data["48RSI"].shift(1) < 30) & (data["48RSI"] >= 30)  # 48RSI从下往上穿30
            & (data["MACD"] < 0)
            & (data["96RSI"] < 50) # 
            
            # ---------------back up----------------
            # ((data["12RSI"] < 20) |(data["12RSI"].shift(1) < 20) | (data["12RSI"].shift(2) < 20))
            
            
            # & (data[f'SMA_{ma_window}_pct'] > -MA_drawdown_low)  # 近10天均值
            # & (data[f'SMA_{ma_window}_pct'] < -2)
            # & ((data["36RSI"] < rsi_36_low) |(data["36RSI"].shift(1) < rsi_36_low) | (data["36RSI"].shift(2) < rsi_36_low))
            # & (data["MACD"] < 0)  # MACD小于0
            # 上涨趋势&rsi下限高;下跌趋势&rsi下限低;
            # & (((data[f"SMA_{ma_window}_pct"] > 0) & (data["240RSI"] < rsi_240_low))| ((data[f"SMA_{ma_window}_pct"] <= 0) & (data["240RSI"] < rsi_240_low - 10)))
            # & (data["95RSI"] < 35)
            # & (data["MACD"] > feature["MACD"].quantile(0.25))  # MACD
        ].index

        sell_strategy_1 = data[
            # 卖出：RSI从上往下穿70 --
            ## row 1: RSI > 70 , row 2: RSI <= 70 , row 2 <-- buy signal
            (data["12RSI"].shift(1) > 70)  # 上一行大于70
            & (data["12RSI"] <= 70)  # 当前行<=70
            # 增长率>万8
            & (data[f"SMA_{ma_window}_pct"] > 8)
            & (data["MACD"] > 0)  # MACD
        ].index

        balance = 100 * 10000  #   起始金额100w
        # 买卖信号
        data.loc[buy_strategy_1, "Buy_Signal"] = 1
        data.loc[sell_strategy_1, "Sell_Signal"] = 1
        # 买卖量
        PositionSizing(data, balance)
        # 计算收益并作图
        profit_cal(data)

        # strategy_1:RSI规律，买点信号白，卖点信号黄
        strategies = [buy_strategy_1, sell_strategy_1]
        colors = ["white", "red"]
        # =================画strategy买卖点==============
        for strategy, color in zip(strategies, colors):
            fig.add_trace(
                go.Scatter(
                    # x=consider_buy["time"],
                    x=strategy,
                    marker=dict(size=6),
                    y=data.loc[strategy.tolist(), "close"],
                    yaxis="y1",
                    mode="markers",
                    name=f"strategy_1",
                    marker_color=color,
                )
            )

        # 实际买卖点位
        actual_buyNsell = [
            data[data["BuyTrade"] != 0].index.tolist(),
            data[data["SellTrade"] != 0].index.tolist(),
        ]
        actual_buyNsell_price = [
            data.loc[data["BuyTrade"] != 0, "close"],
            data.loc[data["SellTrade"] != 0, "close"],
        ]
        colors = ["blue", "red"]
        # =================画strategy买卖点==============
        for bNs, bNs_price, color in zip(
            actual_buyNsell, actual_buyNsell_price, colors
        ):
            fig.add_trace(
                go.Scatter(
                    # x=consider_buy["time"],
                    x=bNs,
                    y=bNs_price + 0.4,
                    yaxis="y1",
                    mode="markers",
                    name="bNs",
                    marker=dict(color=color, size=9, symbol="triangle-down"),
                )
            )

        # 更新布局
        fig.update_layout(
            title="Close and MA",
            xaxis=dict(
                title="时间",
                tickvals=data.index[::1000],  # 用于定位的值
                ticktext=data["time"][::1000],  # 想要显示在 x 轴上的值
                tickangle=45,  # 如果时间标签很长，可以旋转以便阅读
                # rangebreaks=[
                #     dict(bounds=[6, 1], pattern="day of week"),  # 排除周末
                #     dict(values=holidays),  # 排除法定节假日
                #     dict(bounds=[11.51, 13.01], pattern="hour"),  # 排除中午非交易时间
                #     dict(bounds=[15.01, 23], pattern="hour"),  # 排除下午非交易时间
                #     dict(bounds=[0, 9.49], pattern="hour"),  # 排除下午非交易时间
                # ],  # 排除非营业时间（交易时间为9:30-11:30，13:00-15:00）
            ),
            yaxis=dict(
                title="Close Price",  # 左侧 y 轴标题
                titlefont=dict(color="blue"),  # 左侧 y 轴字体颜色
                tickfont=dict(color="blue"),  # 左侧 y 轴刻度颜色
            ),
            yaxis2=dict(
                title="volume",  # 右侧 y 轴标题
                titlefont=dict(color="orange"),  # 右侧 y 轴字体颜色
                tickfont=dict(color="orange"),  # 右侧 y 轴刻度颜色
                overlaying="y",  # 将右侧 y 轴叠加在左侧 y 轴
                side="right",  # 将右侧 y 轴显示在右边
                range=[0, data["volume"].max() * 4],  # 设置右侧 y 轴的显示范围
            ),
            template="plotly",
            legend=dict(x=0.5, y=1.1),  # 设置图例位置
            hovermode="x unified",
            bargap=0.3,  # 调整柱状图之间的间距
        )

        st.title("Those are the good points")
        st.dataframe(feature, height=100)
        st.title("Maybe the good buy points")

        st.dataframe(consider_buy, height=100)
        st.title("股票图像")
        st.plotly_chart(fig)

        # --------MACD-------
        # st.subheader(f"MACD")
        # fig2 = go.Figure()
        # # 绘制dif
        # fig2.add_trace(go.Scatter(x=data['time'], y=macd_dict['dif'],
        #                          yaxis='y1', mode='lines', name='DIF'))
        # # 绘制dea
        # fig2.add_trace(go.Scatter(x=data['time'], y=macd_dict['dea'],
        #                          yaxis='y1', mode='lines', name=f'DEA'))
        # # 绘制柱状图
        # fig2.add_trace(go.Bar(x=data['time'], y=macd_dict['macd'],
        #                      yaxis='y1',name=f'macd'))  # MACD

        # fig2.add_trace(go.Scatter(x=data['time'], y=data['close'],
        #                          yaxis='y2', mode='lines', name='close'))

        # fig2.update_layout(
        #     title="MACD",
        #     xaxis=dict(title="时间"),

        #     yaxis=dict(
        #     title="DIF&DEA",  # 左侧 y 轴标题
        #     titlefont=dict(color='white'),  # 左侧 y 轴字体颜色
        #     tickfont=dict(color='white')  # 左侧 y 轴刻度颜色
        #     ),

        #     yaxis2=dict(
        #     title="close",  # 右侧 y 轴标题
        #     titlefont=dict(color='orange'),  # 右侧 y 轴字体颜色
        #     tickfont=dict(color='orange'),  # 右侧 y 轴刻度颜色
        #     overlaying='y',  # 将右侧 y 轴叠加在左侧 y 轴
        #     side='right'  # 将右侧 y 轴显示在右边
        #     ),

        #     template="plotly_white",
        #     legend=dict(x=0.1, y=1.1),  # 设置图例位置
        #     hovermode="x unified",
        #     bargap=0.3  # 调整柱状图之间的间距
        # )

        # -------RSI-------
        # st.write(RSI_dict)
        # st.subheader(f"RSI")
        # fig3 = go.Figure()
        # fig3.add_trace(go.Scatter(x=data['time'], y=RSI_dict,
        #     yaxis='y1',mode='lines',name=f'RSI'))  # RSI
        # fig3.add_shape(type="line",
        #       x0=data['time'].iloc[0], x1=data['time'].iloc[-1],
        #       y0=70, y1=70,
        #       line=dict(color="red", dash="dash"),
        #       name="Upper Threshold")

        # -----作废-----
        # fig3.update_layout(
        #     title="RSI",
        #     xaxis=dict(title="时间"),

        #     yaxis=dict(
        #     title="RSI",  # 左侧 y 轴标题
        #     titlefont=dict(color='white'),  # 左侧 y 轴字体颜色
        #     tickfont=dict(color='white')  # 左侧 y 轴刻度颜色
        #     ),

        #     template="plotly_white",
        #     legend=dict(x=0.1, y=1.1),  # 设置图例位置
        #     hovermode="x unified",
        #     bargap=0.3  # 调整柱状图之间的间距
        # )

        # fig.update_layout(
        #     xaxis=dict(
        #         rangeselector=dict(
        #             buttons=list([
        #                 dict(count=1, label="1m", step="month", stepmode="backward"),
        #                 dict(count=6, label="6m", step="month", stepmode="backward"),
        #                 # dict(count=1, label="YTD", step="year", stepmode="todate"),
        #                 dict(count=1, label="1y", step="year", stepmode="backward"),
        #                 dict(step="all")
        #             ])
        #         ),
        #         rangeslider=dict(
        #             visible=True
        #         ),
        #         type="date"
        #     )
        # )
        

        # for i in range(12,97,12):
        RSI_window = st.selectbox(
            "请选择RSI参数",
            [12, 24, 48, 96, 240, 360, 720, 1440],
            index=2,
            key="rsi_selectbox_1",
        )

        # 选择后导致全部数据重算
        drawallRSI(data, RSI_window, "white", 1)
        # 画rsi的boll

        st.text(
            f"""
            买点{len(buy_strategy_1.tolist())}个
            卖点{len(sell_strategy_1.tolist())}个
            """
        )

        # st.plotly_chart(fig3, use_container_width=True)

        st.title("Today Factors")
        st.write(data.iloc[-1:])

        # ————————seaborn————————
        # 将数据转换为长格式
        st.title("Data Distribution")
        feature_long = pd.melt(
            feature,
            value_vars=["12RSI","36RSI","48RSI","240RSI", "MACD", "Close-SMA_240(%)", "DIF", "volume"],
            var_name="Metric",
            value_name="Value",
        )
        if feature_long.empty:
            print("数据框为空，请检查数据加载和处理步骤。")
        else:
            g = sns.FacetGrid(
                feature_long,
                col="Metric",
                col_wrap=4,
                height=1,
                sharex=False,
                sharey=False,
            )
            g.figure.set_size_inches(10, 5)  # 设置图表布局：10：5
            # 为每个子集绘制箱线图
            g.map(sns.boxplot, "Value")

            # 添加标题
            g.set_titles(col_template="{col_name}")

            # 显示图表
            st.pyplot(g)

        # sns.set_theme(style="whitegrid")
        # plt.figure(figsize=(10, 6))
        # 使用seaborn的lineplot函数绘制每个SMA列
        # for column in ['SMA_1', 'SMA_2', 'SMA_5']:
        #     sns.lineplot(x='time', y=column, data=data,  size=0.2)
        #     st.write(column)
        # # 添加图例
        # plt.legend()
        # # 设置标题和坐标轴标签
        # plt.title('SMA Time Series')
        # plt.xlabel('Time')
        # plt.ylabel('SMA Values')
        # # 显示图表
        # st.pyplot(plt)

        # drawRSI(data, 'close', 'white', 'RSI', 'red', 0.5)

        # 好买点参数

        st.text(
            f"""
            使用的参数为:RSI:{feature['12RSI'].quantile(0.75)-5:.1f}~{feature['12RSI'].quantile(0.25):.1f}
            Close-SMA_240(%):{feature['Close-SMA_240(%)'].quantile(0.75):.1f}~{feature['Close-SMA_240(%)'].quantile(0.25):.1f}
            MACD:{feature['MACD'].quantile(0.75):.1f}~{feature['MACD'].quantile(0.25):.1f}
            DIF:{feature['DIF'].quantile(0.75):.1f}~{feature['DIF'].quantile(0.25):.1f}
            """
        )

        # 显示数据表
        st.subheader("Data Set")
        st.write(data.head(2))
        st.write(data[["time", "close", "volume"]])
