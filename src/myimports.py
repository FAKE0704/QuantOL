import baostock as bs
import json
import matplotlib.pyplot as plt
import math
import numpy as np
import openpyxl
import pandas as pd
import requests
from sklearn import datasets
from sklearn.model_selection import train_test_split
import time
import websocket  
import xgboost as xgb


from IPython.core.interactiveshell import InteractiveShell 
InteractiveShell.ast_node_interactivity = "all"


def volat(df):
    # 确保time列是日期类型
    df['time'] = pd.to_datetime(df['time'])
    
    # 设置time为索引
    df.set_index('time', inplace=True)
    
    # 计算对数收益率
    df['log_return'] = np.log(df['close'] / df['close'].shift(1))
    
    # 计算日波动率
    df['volatility'] = df['log_return'].std() * np.sqrt(252)
    
    return df['volatility']




# 网格策略_1
def grid_strategy_01(df,st_time,end_time,gridStep):
    # gridStep是百分比
    # 按时间顺序排列
    df = df.sort_values(by='time',ascending=True) 

    # # 根据波动率及股价设定网格长度
    # volatility = volat(df).mean()

    # 起始价格
    st_price = df.loc[df.time==st_time,'close'].iloc[0]
    # 单位格长度
    gridAmount = st_price*gridStep
    #gridNumber记录所在网格号
    df['gridNumber'] = ((df['close']-st_price)/gridAmount).apply(math.ceil)

    # 买卖信号:进入新网格才做操作
    ## 刚触及的问题？
    BuySignal = df.gridNumber.diff() < 0 #如果从上往下穿越网格，就买入
    df.loc[BuySignal,'BuySignal'] = 1  
    df.loc[df['BuySignal']==1,'BuyTrade'] = 1
    df[['BuySignal','BuyTrade']] = df[['BuySignal','BuyTrade']].fillna(0)

    SellSignal = df.gridNumber.diff() > 0  #如果从下往上穿越网格，就卖出
    df.loc[SellSignal,'SellSignal'] = 1
    df['SellSignal'] = df['SellSignal'].fillna(0)
    df.loc[df['SellSignal']==1,'SellTrade'] = 1
    df['SellTrade'] = df['SellTrade'].fillna(0)

    df[['BuySignal','SellSignal','BuyTrade','SellTrade']] = df[['BuySignal','SellSignal','BuyTrade','SellTrade']].fillna(0)
    
    return df
    

# 网格策略_2
def grid_strategy_alpha01(df,st_time,end_time,gridStep):
    # gridStep是百分比
    ## 根据波动率及股价设定网格长度
    # volatility = volat(df).mean()

    # 起始价格
    st_price = df.loc[df.time==st_time,'close'].iloc[0]
    # 单位格长度
    gridAmount = st_price*gridStep
    #gridNumber记录所在网格号
    df['gridNumber'] = ((df['close']-st_price)/gridAmount).apply(math.ceil)

    # 买卖信号:进入新网格才做操作
    ## 刚触及的问题？？
    BuySignal = df.gridNumber.diff() < 0
    df.loc[BuySignal,'BuySignal'] = 1
    df.loc[(df['BuySignal']==1)&(df['gridNumber']<=10),'BuyTrade'] = (2.0 * (10-df['gridNumber']))
    df.loc[(df['BuySignal']==1)&(df['gridNumber']>10),'BuyTrade'] = 0
    df[['BuySignal','BuyTrade']] = df[['BuySignal','BuyTrade']].fillna(0)


    SellSignal = df.gridNumber.diff() > 0
    df.loc[SellSignal,'SellSignal'] = 1
    df['SellSignal'] = df['SellSignal'].fillna(0)
    # df.loc[df['SellSignal']==1,'SellTrade'] = 2 * (abs(df['gridNumber'])-1)

    try:
        df.loc[(df['SellSignal']==1)&(df['gridNumber']>=-10),'SellTrade'] = (2.0 * (10+df['gridNumber']))
    except ValueError as e:
        print(df[(abs(df['gridNumber'])-1)<0])
    df['SellTrade'] = df['SellTrade'].fillna(0)
    # 卖出必须得有得卖
    SellSignal_Modify = (df['SellTrade'].cumsum()>df['BuyTrade'].cumsum())
    df.loc[SellSignal_Modify,'SellSignal'] = 0
    df.loc[SellSignal_Modify,'SellTrade'] = 0
    
    df[['BuySignal','SellSignal','BuyTrade','SellTrade']] = df[['BuySignal','SellSignal','BuyTrade','SellTrade']].fillna(0)
    
    return df
    

# 指标计算
# calculate last-n days Moving Average(MA), and assign to df['nMA']


def nMA(n,df,price):
    df["{}MA".format(n)]=df[price].rolling(window=n).mean().shift(1)
    # null value processing
    return df

# calculate DIF = mMA-nMA; e.g.:DIF=7MA-14MA
def DIF(m,n,df):
    df["DIF"] = df["{}MA".format(m)]-df["{}MA".format(n)]
    return df

# calculate nDIF
def nDIF(n,df):
    df["{}DIF".format(n)]=df['DIF'].rolling(window=n).mean().shift(1)
    return df

# calculate MACD
def  MACD(n,df):
    df["{}MACD".format(n)]=df['DIF']-df["{}DIF".format(n)]
    return df

# 计算n天sigma值
def nsigma(n,df,price):
    df["{}sigma".format(n)] = df[price].rolling(window=n).std(ddof=0).shift(1)
    return df

def set_index(n,df,price):
    nMA(n,df,price)
    nsigma(n,df,price)


def BOLL(BOLL_lambda,n,df,price):
    # 绘BOLL图
    fig = plt.figure(figsize=(30, 5))  # 设置图形的大小
    _=plt.plot(df[price], label=price,lw=0.08, color = 'black')  # 绘制收盘价
    _=plt.plot(df["{}MA".format(n)], label="{}MA".format(n),lw=0.027, color = 'yellow')  # 绘制n均线
    _=plt.plot(df["{}MA".format(n)]-BOLL_lambda*df["{}sigma".format(n)], lw=0.027, color = 'blue')  # 绘制下板，使用BOLL_lambda倍sigma
    _=plt.plot(df["{}MA".format(n)]+BOLL_lambda*df["{}sigma".format(n)], lw=0.027, color = 'red')  #  绘制上板，使用BOLL_lambda倍sigma
    
    # 设定买卖信号
    df['SellSignal']=0;df['BuySignal']=0
    df.loc[df[price]>df["{}MA".format(n)] + BOLL_lambda*df["{}sigma".format(n)], 'SellSignal']=1  #顶部点位
    df.loc[df[price]<df["{}MA".format(n)] - BOLL_lambda*df["{}sigma".format(n)], 'BuySignal']=1  #底部点位
    
    # 设定买卖量
    df['SellTrade']=0;df['BuyTrade']=0
    df.loc[df['SellSignal']==1, 'SellTrade']=1; df.loc[df['BuySignal']==1, 'BuyTrade']=1
    p_buychance = (df['SellSignal']==1).sum()/len(df['SellSignal'])*100
    p_sellchance = (df['BuySignal']==1).sum()/len(df['BuySignal'])*100
    print(f"BOLL策略：\n"
      f"使用{n}MA均线，{BOLL_lambda}个sigma间隔；\n"
      f"买入规则-i日收盘价小于【{n}MA-{BOLL_lambda}*{n}sigma】，则在i+1日买入\n"
      f"卖出规则-i日收盘价大于【{n}MA+{BOLL_lambda}*{n}sigma】，则在i+1日卖出\n"
      f"回测买入点占比：{p_buychance:.2f}\n"
      f"回测卖出点占比：{p_sellchance:.2f}")
    return fig
    #_=plt.tick_params(axis='y', labelcolor='black')

# 做利润图
# def proft_plot(df):
#     fig = plt.figure(figsize=(30, 5))  # 设置图形的大小
#     _=plt.plot(df[''], label=price,lw=0.027, color = 'black')  # 绘制收盘价
#     _=plt.plot(df["{}MA".format(n)], label="{}MA".format(n),lw=0.027, color = 'yellow')  # 绘制n均线
#     _=plt.plot(df["{}MA".format(n)]-BOLL_lambda*df["{}sigma".format(n)], lw=0.027, color = 'blue')  # 绘制下板，使用BOLL_lambda倍sigma
#     _=plt.plot(df["{}MA".format(n)]+BOLL_lambda*df["{}sigma".format(n)], lw=0.027, color = 'red')  #  绘制上板，使用BOLL_lambda倍sigma    



#### 获取沪深A股历史K线数据 ####
# 详细指标参数，参见“历史行情指标参数”章节；“分钟线”参数与“日线”参数不同。“分钟线”不包含指数。
# 分钟线指标：date,time,code,open,high,low,close,volume,amount,adjustflag
# 周月线指标：date,code,open,high,low,close,volume,amount,adjustflag,turn,pctChg

def get_stock_data(stock_code,start_date,end_date,frequency):
    lg = bs.login()
    rs = bs.query_history_k_data_plus(stock_code,
        "date,time,code,open,high,low,close,volume,amount,adjustflag",
        start_date=start_date, end_date=end_date,
        frequency=frequency, adjustflag="3")
    #### 打印结果集 ####
    data_list = []
    while (rs.error_code == '0') & rs.next():
        # 获取一条记录，将记录合并在一起
        data_list.append(rs.get_row_data())
    result = pd.DataFrame(data_list, columns=rs.fields)
    return result