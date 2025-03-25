import pandas as pd
from datetime import datetime, timedelta
import os
from .baostock_source import BaostockDataSource

class Data:
    """数据接口"""
    
    def __init__(self, name: str, frequency: str, data_source: BaostockDataSource = None):
        """
        初始化数据对象
        :param name: 股票名称
        :param frequency: 数据频率
        :param data_source: 数据源实例，默认为None时会创建默认BaostockDataSource
        """
        self.stock_code: str = None
        self.start_date: str = None
        self.end_date: str = None
        self.frequency: str = frequency
        self.name: str = name
        self.data_source = data_source or BaostockDataSource(
            frequency=frequency,
            cache_dir="../data_cache"
        )
        self.sma = pd.DataFrame()
        self.macd = pd.DataFrame()
        self.rsi = pd.DataFrame()
        self.high = pd.DataFrame()
        self.volume = pd.DataFrame()
        self.strategy = [{"name": "策略名", "strategy": "逻辑"}]
        self.data = None
        self.load()
        
        

    def load(self):
        """
        加载截止今日最近的全部最新数据。
        """
        script_path = os.path.abspath(__file__)
        directory_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(script_path))), "Data"
        )
        stock_info = os.path.join(directory_path, "股票信息.xlsx")
        df = pd.read_excel(stock_info)

        # 根据freq的不同,使用不同方式
        if df.loc[df["code_name"] == self.name, :].empty:
            print(f"{self.name}-不存在，请确认名称")
        else:
            self.stock_code = df.loc[df["code_name"] == self.name, "code"].iloc[
                0
            ]  # string
        self.start_date = pd.to_datetime(
            df.loc[df["code"] == self.stock_code, "ipoDate"].iloc[0]
        ).strftime(
            "%Y-%m-%d"
        )  # string
        self.path = os.path.join(
            directory_path, f"{self.name}{self.frequency}数据.xlsx"
        )

        end_date = df.loc[df["code"] == self.stock_code, "outDate"]

        # 若有数据可以读,则读取数据,若没有,则获取新数据
        # print(os.path.isfile(self.path)) # test
        if os.path.isfile(self.path):
            data = pd.read_excel(self.path, index_col=None)
            data = data.astype({
                'date': 'datetime64[ns]',
                'close': 'float64',
                'high': 'float64',
                'open': 'float64',
                'low': 'float64',
                'volume': 'int64'
            })

            # 处理时间字段
            if 'time' in data.columns and self.frequency in ["1", "5", "15", "30", "60"]:
                data['time'] = pd.to_datetime(data['time'], format="%Y%m%d%H%M")
            
            self.data = data
            print(f"==={self.name}数据加载完成!==")
    # def update_data_m(self,)

    async def update_data(self, data_end_date):
        """
        异步更新单个股票的数据
        """
        try:
            new_data = await self.data_source.load_data(
                self.stock_code,
                data_end_date,
                self.end_date,
                self.frequency
            )
            
            # 合并新旧数据
            self.data = pd.concat([self.data, new_data]).drop_duplicates(subset=['date'])
            print(f"{self.name}数据已成功更新")
        except Exception as e:
            print(f"更新数据时出错: {str(e)}")
            raise

    def delete(self):
        """
        load完之后觉得数据不对的话,删掉咯
        """
        os.remove(self.path)

    def delete_last(self):
        """
        删掉data最后一行
        """
        self.data = self.data.drop(self.data.index[-1])

    def set_time_interval(self, start_time, end_time):
        data = self.data
        data = data[(data["time"] > start_time) & (data["time"] < end_time)]
        data = data.reset_index(drop=True)
        self.data = data

    def get_sma(self, window):
        if f"SMA_{window}" in self.sma.columns:
            pass
        else:
            sma = self.data["close"].rolling(window=window).mean().shift(1)
            self.sma[f"SMA_{window}"] = sma
        return self.sma[f"SMA_{window}"]

    def get_sema(self, window):
        if f"SEMA_{window}" in self.macd.columns:
            pass
        else:
            sema = self.data["close"].ewm(span=window, adjust=False).mean().shift(1)
            self.macd[f"SEMA_{window}"] = sema
        return self.macd[f"SEMA_{window}"]

    def get_dif(self, short_window, long_window):
        if f"DIF_{short_window}_{long_window}" in self.macd.columns:
            pass
        else:
            # short window EMA
            sema = self.get_sema(short_window)
            # long window EMA
            lema = self.get_sema(short_window)
            dif = sema - lema
            self.macd[f"DIF_{short_window}_{long_window}"] = dif
        return self.macd[f"DIF_{short_window}_{long_window}"]

    def get_dea(self, short_window, signal_window, long_window):
        if f"DEA_{short_window}_{signal_window}_{long_window}" in self.macd.columns:
            pass
        else:
            dif = self.get_dif(short_window, long_window)
            dea = dif.ewm(span=signal_window, adjust=False).mean().shift(1)
            self.macd[f"DEA_{short_window}_{signal_window}_{long_window}"] = dea
        return self.macd[f"DEA_{short_window}_{signal_window}_{long_window}"]

    def get_macd(self, short_window:int, signal_window:int, long_window:int):
        if f"MACD_{short_window}_{signal_window}_{long_window}" in self.macd.columns:
            pass
        else:
            # DIF
            dif = self.get_dif(short_window, long_window)
            # DEA
            dea = self.get_dea(short_window, signal_window, long_window)

            # MACD柱状图计算
            macd = (dif - dea) * 2
            self.macd[f"MACD_{short_window}_{signal_window}_{long_window}"] = macd
        return self.macd[f"MACD_{short_window}_{signal_window}_{long_window}"]

    def get_rsi(self, window):
        """
        根据第n日结束时数据计算的指标会放在第n+1日
        """
        if f"RSI_{window}" in self.rsi.columns:
            pass
        else:
            # 计算收盘价的变化值
            delta = self.data["close"].diff()
            # 将上涨和下跌分别计算
            gain = delta.clip(lower=0)  # 涨幅，负值裁剪为 0
            loss = -delta.clip(upper=0)  # 跌幅，正值裁剪为 0
            # 计算平均上涨和平均下跌
            avg_gain = gain.rolling(window=window).mean().shift(1)  # 上涨的均值
            avg_loss = loss.rolling(window=window).mean().shift(1)  # 下跌的均值
            # 计算 RS（相对强弱值）
            rs = avg_gain / avg_loss
            # 计算 RSI
            self.rsi[f"RSI_{window}"] = 100 - (100 / (1 + rs))
        return self.rsi[f"RSI_{window}"]

    def get_high(self, window):
        if f"HIGH_{window}" in self.high.columns:
            pass
        else:
            # 计算近 window 日的最高价
            high = self.data["high"].rolling(window=window).max().shift(1)
            # # 填充缺失值
            # high = high.fillna(method='ffill')
            # 保存到 self.high 中
            self.high[f"HIGH_{window}"] = high
        return self.high[f"HIGH_{window}"]

    def get_volume_sum(self, window):
        if f"SUM_{window}" in self.volume.columns:
            pass
        else:
            # 计算近 window 内的volume和
            volume = self.data["volume"].rolling(window=window).sum().shift(1)
            self.volume[f"SUM_{window}"] = volume
        return self.volume[f"SUM_{window}"]

    def get_volume_avg(self, window):
        if f"AVG_{window}" in self.volume.columns:
            pass
        else:
            # 计算近 window 内的volume均值
            volume = self.data["volume"].rolling(window=window).mean().shift(1)
            self.volume[f"AVG_{window}"] = volume
        return self.volume[f"AVG_{window}"]

    def get_volume_ratio(self, window):
        """
        今天的volume不会在分母。
        """
        if f"RATIO_{window}" in self.volume.columns:
            pass
        else:
            # 计算近 window 内的volume和
            avg = self.get_volume_avg(window)
            volume = self.data["volume"] / avg
            self.volume[f"RATIO_{window}"] = volume
        return self.volume[f"RATIO_{window}"]

    def get_volume_high(self, window):
        if f"HIGH_{window}" in self.volume.columns:
            pass
        else:
            # 计算近 window 日的最高量
            volume = self.data["volume"].rolling(window=window).max().shift(1)

            self.volume[f"HIGH_{window}"] = volume
        return self.volume[f"HIGH_{window}"]

    



    

####################Database#################
def update_data2():
    """
    update to  database
    """

    config = {
        "user": "gpf",
        "password": "163452",
        # 'host': '192.168.5.109',
        "host": "127.0.0.1",
        "database": "mydatabase",
        "port": 3306,
    }
    conn = mysql.connector.connect(**config)

    cursor = conn.cursor()

    cursor.execute(
        "insert into customers (name, address) values ('John', 'Highway 21')"
    )

    # 提交事务
    conn.commit()

    cursor.execute("select * from customers")
    info = cursor.fetchall()

    print(info)  # 打印查询结果

    # 关闭连接
    cursor.close()
    conn.close()


    

################# basic method#############
def get_stock_data(stock_code, start_date, end_date, frequency):
    """
    更新某个日期的单个股票的数据
    stock_code：string,
    start_date：string, "2025-01-01"
    end_date：string, "2025-01-31"
    frequency：
    """
    lg = bs.login()
    if frequency in ["1", "5", "15", "30", "60"]:
        print("正在获取中短期数据...")
        rs = bs.query_history_k_data_plus(
            stock_code,
            "date,time,code,open,high,low,close,volume,amount,adjustflag",
            start_date=start_date,
            end_date=end_date,
            frequency=frequency,
            adjustflag="3",
        )
    else:
        rs = bs.query_history_k_data_plus(
            stock_code,
            "date,code,open,high,low,close,preclose,volume,amount,adjustflag,turn,tradestatus,pctChg,isST",
            start_date=start_date,
            end_date=end_date,
            frequency=frequency,
            adjustflag="3",
        )
    #### 打印结果集 ####
    data_list = []  

    if rs == None:
        print(
            f"未从baostock获取到数据,参数有误；传入参数为{stock_code},{start_date},{end_date},{frequency}"
        )
    else:
        while (rs.error_code == "0") & rs.next():
            # 获取一条记录，将记录合并在一起
            data_list.append(rs.get_row_data())

        result = pd.DataFrame(data_list, columns=rs.fields)
        # print(type(result['time'].iloc[0])) # debug
        # print(type(result['date'].iloc[0])) # debug
        bs.logout()
        return result


def get_stock_info(stock_code, start_date, end_date, frequency):
    """
    更新某个日期的单个股票的数据
    stock_code：
    start_date：string,
    end_date：string,
    frequency：
    """

    lg = bs.login()
    rs = bs.query_history_k_data_plus(
        stock_code,
        "date,time,code,open,high,low,close,volume,amount,adjustflag",
        start_date=start_date,
        end_date=end_date,
        frequency=frequency,
        adjustflag="3",
    )
    #### 打印结果集 ####

    data_list = []
    while (rs.error_code == "0") & rs.next():
        # 获取一条记录，将记录合并在一起
        data_list.append(rs.get_row_data())
    bs.logout()

    # 转换为 DataFrame
    result = pd.DataFrame(data_list, columns=rs.fields)

    # 检查是否有数据
    if result.empty:
        print("未找到该股票的信息，请检查股票代码是否正确。")
        return None
    else:
        # 获取上市日期
        start_date = result.loc[0, "ipoDate"]
        return start_date, result

    return result


def update_info():
    """
    更新所有股票的信息。并保存到
    """
    # 登录Baostock
    lg = bs.login()

    # 显示登录返回信息
    print("login respond error_code: " + lg.error_code)
    print("login respond error_msg: " + lg.error_msg)

    # 获取证券基本资料
    # 这里我们查询所有A股股票的基本信息
    rs = bs.query_stock_basic()

    #### 打印结果集 ####
    data_list = []
    while (rs.error_code == "0") & rs.next():
        # 获取一条记录，将记录合并在一起
        data_list.append(rs.get_row_data())
    result = pd.DataFrame(data_list, columns=rs.fields)
    # 登出系统
    result.to_excel("../../Data/股票信息.xlsx", index=False)
    bs.logout()


if __name__ == "__main__":
    pass
    # update_data("sh.000001","5") #上证指数：sh.000001
