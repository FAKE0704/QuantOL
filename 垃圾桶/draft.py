import pandas as pd
import os

# 打印当前工作目录
print(os.getcwd())



# 检查文件是否存在
file_path = '/VSC_work/Data/光大嘉宝最新数据.xlsx'
print(os.path.exists(file_path))

file_extension = file_path.split('.')[-1].lower()

print(file_extension)
# 判断文件类型
if file_extension in ['csv']:
    data = pd.read_csv(file_path)
elif file_extension in ['xlsx']:
    data = pd.read_excel(file_path, engine="openpyxl")
else:
    st.error(f"不支持的文件类型：{file_extension}")



import plotly.graph_objects as go

# 创建一个基本的图形
fig = go.Figure()

# 添加第一个 trace，使用默认的 x 轴和 y 轴
fig.add_trace(go.Scatter(x=[1, 2, 3, 4, 5], y=[10, 20, 30, 40, 50], name='Trace 1',
                         line=dict(color='blue'), mode='lines+markers'))

# 添加第二个 trace，使用第二个 x 轴和第二个 y 轴
fig.add_trace(go.Scatter(x=[10, 20, 30, 40, 50], y=[100, 200, 300, 400, 500], name='Trace 2',
                         line=dict(color='red'), mode='lines+markers',
                         xaxis='x2', yaxis='y2'))

# 配置布局，定义第二个 x 轴和 y 轴的位置和属性
fig.update_layout(
    xaxis=dict(
        title='X1 Axis',
        domain=[0, 0.45]  # 第一个 x 轴的范围
    ),
    xaxis2=dict(
        title='X2 Axis',
        domain=[0.55, 1]  # 第二个 x 轴的范围
    ),
    yaxis=dict(
        title='Y1 Axis',
        domain=[0, 0.45]  # 第一个 y 轴的范围
    ),
    yaxis2=dict(
        title='Y2 Axis',
        domain=[0.55, 1]  # 第二个 y 轴的范围
    ),
    title='Two Axes Example'
)

# 显示图形
fig.show()


# sg 1
buy_strategy = data[
        # 买入：48RSI从下往上穿30 --
        ## row 1: RSI < 30 , row 2: RSI >= 30 , row 2 <-- buy signal
        (data["48RSI"].shift(1) < 30) & (data["48RSI"] >= 30)  # 48RSI从下往上穿30
        & (data["MACD"] < 0)
    ].index

    sell_strategy_1 = data[
        # 卖出：RSI从上往下穿70 --
        ## row 1: RSI > 70 , row 2: RSI <= 70 , row 2 <-- buy signal
        (data["48RSI"].shift(1) > 70)  # 上一行大于70
        & (data["48RSI"] <= 70)  # 当前行<=70
        # 增长率>万8
        & (data[f"SMA_{ma_window}_pct"] > 8)
        & (data["MACD"] > 0)  # MACD
    ].index


# sg 2
buy_strategy_1 = data[
        # 买入：48RSI从下往上穿30 --
        ## row 1: RSI < 30 , row 2: RSI >= 30 , row 2 <-- buy signal
        (data["12RSI"].shift(1) < 30) & (data["36RSI"] >= 30)  # 48RSI从下往上穿30
        & (data["720RSI"] <= 45)
        & (data["MACD"] < 0)
    ].index

    sell_strategy_1 = data[
        # 卖出：RSI从上往下穿70 --
        ## row 1: RSI > 70 , row 2: RSI <= 70 , row 2 <-- buy signal
        (data["48RSI"].shift(1) > 70)  # 上一行大于70
        & (data["48RSI"] <= 70)  # 当前行<=70
        # 增长率>万8
        & (data[f"SMA_{ma_window}_pct"] > 8)
        & (data["MACD"] > 0)  # MACD
    ].index

# sg 3
buy_strategy_1 = data[
        # 买入：48RSI从下往上穿30 --
        ## row 1: RSI < 30 , row 2: RSI >= 30 , row 2 <-- buy signal
        ((data["720RSI"]<50)&((data["48RSI"].shift(1) < 30) & (data["48RSI"] >= 30)))
        |((data["720RSI"]>=50)&((data["48RSI"].shift(1) < 40) & (data["48RSI"] >= 40)))  # 48RSI从下往上穿35
        & (data["MACD"] < 0)
        #& (data["12RSI"] <= 30)
        # & (data[f"SMA_{ma_window}_pct"] > -8)
        # & (data["720RSI"].shift(5)/data["720RSI"] < 1)  # 720RSI上扬？
        # & ((data["720RSI"].isna())|(data["720RSI"] <= 50))
        
        
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
        (data["48RSI"].shift(1) > 70)  # 上一行大于70
        & (data["48RSI"] <= 70)  # 当前行<=70
        # 增长率>万8
        & (data[f"SMA_{ma_window}_pct"] > 3)
        & (data["MACD"] > 0)  # MACD
    ].index