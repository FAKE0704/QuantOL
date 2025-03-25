import streamlit as st
import pandas as pd
# import chinese_calendar as cc
import openpyxl
import os

st.set_page_config(
    page_icon="🧊",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://www.extremelycoolapp.com/help',
        'Report a bug': "https://www.extremelycoolapp.com/bug",
        'About': "# This is a header. This is an *extremely* cool app!"
    }
)

@st.cache_data  # 使用缓存装饰器，存储数据处理结果
def load_data(file_path):
    file_extension = file_path.split(".")[-1].lower()

    full_file_path = os.path.join(os.getcwd(),"Data",file_path)
    # 判断文件类型
    if file_extension in ["csv"]:
        data = pd.read_csv(full_file_path)
    elif file_extension in ["xlsx"]:
        data = pd.read_excel(full_file_path, engine="openpyxl")
    else:
        st.error(f"不支持的文件类型：{file_extension}")

    # 确保时间列time为datetime格式
    if "time" not in data.columns and "close" in data.columns:  # 数据集没有time列
        data["time"] = pd.to_datetime(data["date"])  # 统一使用time代表时间
    else:
        # 提取需要的部分并格式化
        data["time"] = data["time"].astype(str).str[:12]
        data["time"] = pd.to_datetime(data["time"], format="%Y%m%d%H%M")

    # 按时间排序
    data.sort_values(by="time", inplace=True)
    data.reset_index(drop=True)
    return data


@st.cache_data  # 预计算所有可能的移动平均线
def precompute_SMA(data, max_window):
    ma_dict = {}
    for window in range(1, max_window + 1):
        data[f"SMA_{window}"] = (
            data["close"].rolling(window=window).mean().shift(1)
        )  # 向下移动一行
        ma_dict[window] = data[f"SMA_{window}"]
    data["Close-SMA_240(%)"] = (data["close"] - data["SMA_240"]) / data["close"] * 100
    return ma_dict, data


@st.cache_data  # 预计算所有可能的MACD
def precompute_MACD(data, short_window, long_window, signal_window):
    macd_dict = {}
    # short window EMA
    data[f"SEMA_{short_window}"] = (
        data["close"].ewm(span=short_window, adjust=False).mean().shift(1)
    )
    short_ema = data[f"SEMA_{short_window}"]
    # long window EMA
    data[f"LEMA_{long_window}"] = (
        data["close"].ewm(span=long_window, adjust=False).mean().shift(1)
    )
    long_ema = data[f"LEMA_{long_window}"]
    # DIF
    data[f"DIF"] = short_ema - long_ema
    dif = data[f"DIF"]
    # DEA线计算
    data[f"DEA_{signal_window}"] = (
        dif.ewm(span=signal_window, adjust=False).mean().shift(1)
    )
    dea = data[f"DEA_{signal_window}"]
    # MACD柱状图计算
    data[f"MACD"] = (dif - dea) * 2
    macd = data[f"MACD"]
    macd_dict = {"dif": dif, "dea": dea, "macd": macd}
    return macd_dict, data


@st.cache_data  # 预计算所有可能的RSI
def precompute_RSI(df, window):
    """
    计算 n 日 RSI 指标
    :param df: 包含 open 和 close 列的 DataFrame
    :param window: RSI 指标的周期
    :return: 返回添加 RSI 列的 DataFrame
    """
    rsi_dict = {}
    for window in range(2,window):
        # 计算收盘价的变化值
        delta = df["close"].diff()
        # 将上涨和下跌分别计算
        gain = delta.clip(lower=0)  # 涨幅，负值裁剪为 0
        loss = -delta.clip(upper=0)  # 跌幅，正值裁剪为 0
        # 计算平均上涨和平均下跌
        avg_gain = gain.rolling(window=window).mean().shift(1)  # 上涨的均值
        avg_loss = loss.rolling(window=window).mean().shift(1)  # 下跌的均值
        # 计算 RS（相对强弱值）
        rs = avg_gain / avg_loss
        # 计算 RSI
        df[f"{window}RSI"] = 100 - (100 / (1 + rs))
    return df["12RSI"], df

@st.cache_data
def precompute_profit_opportunities(
    df, price_col="close", time_col="time", profit_threshold=0.1
):
    """
    绘制历史中所有能赚profit_threshold%利润的机会。

    参数:
    - df: 包含股票数据的 DataFrame
    - price_col: 价格列的名称，默认为 'close'
    - time_col: 时间列的名称，默认为 'time'
    - profit_threshold: 利润阈值，默认是 10% (0.1)
    """

    # 初始化变量
    opportunities = []  # 保存找到的 (lowpoint, highpoint) 机会
    low_index = 0  # 当前 lowpoint 的索引

    # 遍历价格数据
    for i in range(1, len(df)):
        current_price = df.loc[i, price_col]  # 当前价格
        low_price = df.loc[low_index, price_col]  # 当前 lowpoint 价格

        # 判断是否更新 lowpoint
        if current_price < low_price:
            low_index = i  # 更新 lowpoint 为当前索引
        else:
            # 计算价差比例
            price_diff_ratio = (current_price - low_price) / low_price

            # 如果价差超过利润阈值，记录为 highpoint
            if price_diff_ratio >= profit_threshold:
                high_index = i  # highpoint 索引
                high_price = df.loc[high_index, price_col]
                opportunities.append((low_index, low_price,high_index, high_price))  # 记录机会

                # 从 highpoint 的下一天重新设置 lowpoint
                if i + 1 < len(df):  # 防止越界
                    low_index = i + 1
    return opportunities


def get_china_holidays(year):
    holidays = []
    start_date = pd.Timestamp(f"{year}-01-01")
    end_date = pd.Timestamp(f"{year}-12-31")
    current_date = start_date

    while current_date <= end_date:
        if cc.is_holiday(current_date):  # 检查是否是法定节假日
            holidays.append(current_date)
        current_date += pd.Timedelta(days=1)

    return holidays

def set_factor():
    # 最大窗口大小选择框
    max_window = st.selectbox("请选择最大窗口大小", [14, 48, 96, 240, 360], index=4)
    
    # 创建一个列的布局，一行放四个选择框
    col1, col2, col3, col4 = st.columns(4)

    
    # RSI参数选择框
    with col1:
        RSI_parameter = st.selectbox("请选择RSI参数", [12,  48, 96, 240,720,1440, 2880], index=6) # 1小时，1天，2天，5天，15天，30天,60天

        

    
    # 短期窗口大小选择框
    with col2:
        short_window = st.selectbox(
            "请选择短期窗口大小", [6, 12, 48, 96, 240,720,1440], index=1
        )
        
    
    # 信号窗口大小选择框
    with col3:
        signal_window = st.selectbox("请选择信号窗口大小", [9, 25, 72, 168 ,480,1080 ], index=1)

        

    # 长期窗口大小选择框
    with col4:
        long_window = st.selectbox("请选择长期窗口大小", [12,  48, 96, 240,720,1440], index=1)

   
    
    # 利润阈值选择框
    profit_threshold = st.text_input("请输入利润阈值(%):", value="20")

    profit_threshold = float(profit_threshold) / 100

    # strategy 参数
    col1, col2, col3 = st.columns(3)
    with col1:
        MA_drawdown_low = st.text_input("请输入MA跌幅下限(万分之):", value="7")
        MA_drawdown_low = float(MA_drawdown_low)
    with col2:
        rsi_36_low = st.text_input("36RSI必须低于:", value="33")
        rsi_36_low = float(rsi_36_low)
    with col3:
        rsi_240_low = st.text_input("240RSI必须低于:", value="30")
        rsi_240_low = float(rsi_240_low)




    return (
        max_window,
        RSI_parameter,
        short_window,
        long_window,
        signal_window,
        profit_threshold,
        MA_drawdown_low,
        rsi_36_low,
        rsi_240_low,
    )
