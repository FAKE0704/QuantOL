import numpy as np
import streamlit as st
import plotly.graph_objects as go
from tqdm import tqdm
import time
import pandas as pd
from pandas import Series
from src.data.database import Strategy
from src.data.database import Data


class BackTesting:
    """
    一个策略产生的买卖信号,可能会对应多个执行结果
    """

    def __init__(self, strategy):
        self.risk_free_rate: float = 0.03  # 无风险利率, 通常假设为存款利率
        self.tradeDay: int = 252  # 交易日数,通常a股一年252个交易日
        self.balance_init: float = 100 * 10000  # 余额,初始资金一百万
        self.serviceFee: float = 5 / 10000  # 手续费万分之5

        # 行动前
        self.balance: Series = pd.Series([self.balance_init])  # 子弹
        self.asset: Series = pd.Series([self.balance_init])  # 总资产
        self.position: Series = pd.Series([0])  # 持仓资金
        self.positionAmount: Series = pd.Series([0])

        # 后结算
        self.Strategy: Strategy = strategy
        self.Data: Data = strategy.Data
        self.buyTrade: Series = pd.Series([0])  # 买入量
        self.buyAmount: Series = pd.Series([0])  # 买入金额
        self.sellTrade: Series = pd.Series([0])
        self.sellAmount: Series = pd.Series([0])
        self.sellPrice: Series = pd.Series([0])  # 售出价格，与收盘价不同
        self.cost: Series = pd.Series([0])
        self.revenue: Series = pd.Series([0])
        self.profit: Series = pd.Series([0])  #
        self.profit_cum: Series = pd.Series([0])  # 累计净收益
        self.profit_ma: Series = pd.Series([0])
        self.roi: Series = pd.Series([0])  # 累计收益率
        self.roi_pct: Series = pd.Series([0])
        self.drawdown: Series = pd.Series([0])
        self.drawdown_max: Series = pd.Series([0])
        self.drawdown_pct: Series = pd.Series([0])

        self.backtest()

    @st.cache_resource
    def fixed_position(_self):
        """
        买入量 = 卖出量 = 资金可购买股数/100

        更新buy,sell,position
        """
        # _self.Strategy.Data.data.loc[:,'close'] = _self.Strategy.Data.data.loc[:,'close'].astype(float)

        # 计算1%加仓仓位
        fixed_position = int(
            int(_self.balance_init / _self.Strategy.Data.data.loc[0, "close"] / 100)
            / 100
        )  # 1代表100股

        # 记录上次买卖价格
        last_buy = None
        last_buy_index = 0

        # 对于时刻i，如果有signal，signal是否用了i时数据？——不该用
        for i in tqdm(
            range(1, len(_self.Strategy.Data.data)),
            desc="进度条",
            unit="%",
            leave=False,
        ):

            # 计算买入量buytrade -----先写一个简单的买入卖出
            buytrade = fixed_position * 100  # 买入股数
            if _self.Strategy.buySignal.iloc[i] == True:  # 有买入信号;
                if (  # 钱包余额-预备买入金额＞0
                    _self.balance.iloc[i - 1]
                    - buytrade * _self.Strategy.Data.data.loc[i - 1, "close"]
                    > 0
                ):
                    if (last_buy == None) or (  # 首次购买 或  与上次买入价相比已跌3%
                        abs(
                            (_self.Strategy.Data.data.loc[i - 1, "close"] - last_buy)
                            / last_buy
                        )
                        > 0.03
                    ):
                        _self.buyTrade.loc[len(_self.buyTrade)] = buytrade
                        # print("买入成功！：\nindex：", i,
                        #     "\n时间：",_self.Strategy.Data.data.loc[i,'time'],
                        #     "\n(今日)买入价：（根据截止今早的数据分析信号）",_self.Strategy.Data.data.loc[i,'close'],
                        #     #   "\n成本价(昨日)：",_self.Strategy.Data.data.loc[i-1，'']
                        #     "\n上次买入价：",last_buy,
                        #     "\n"
                        # )

                        last_buy = _self.Strategy.Data.data.loc[
                            i - 1, "close"
                        ]  # 买入更新上次买入记录
                        last_buy_index = i
                    else:
                        _self.buyTrade.loc[len(_self.buyTrade)] = 0
                        # print("拒绝买入！两次买入价差异小于3\%\nindex：", i,
                        #     "\n时间：",_self.Strategy.Data.data.loc[i,'time'],
                        #     "\n买入价：",_self.Strategy.Data.data.loc[i,'close'],
                        #     #   "\n成本价(昨日)：",_self.Strategy.Data.data.loc[i-1，'']
                        #     "\n上次买入价：",last_buy,
                        #     "\n两次买入变化幅度：",abs((_self.Strategy.Data.data.loc[i,'close']-last_buy)/last_buy)*100,
                        #     "\n"
                        # )
                else:  # 买不起
                    _self.buyTrade.loc[len(_self.buyTrade)] = 0
                # print("拒绝买入！余额不足。你可能错过了买入机会。\nindex：", i,
                #     "\n时间：",_self.Strategy.Data.data.loc[i,'time'],
                #     "\n(昨日)钱包余额:",_self.Strategy.Data.data.loc[i - 1, "Balance"],
                #     '\n买入x股:',buytrade,
                #     '\n准备买入金额:',buytrade * _self.Strategy.Data.data.loc[i, "close"],
                #     "\n买入价：",_self.Strategy.Data.data.loc[i,'close'],
                #     #   "\n成本价(昨日)：",_self.Strategy.Data.data.loc[i-1，'']
                #     "\n上次买入价：",last_buy,
                #     "\n两次买入变化幅度：",abs((_self.Strategy.Data.data.loc[i,'close']-last_buy)/last_buy)*100,
                #     "\n"
                # )
            else:  # 没有买入信号
                _self.buyTrade.loc[len(_self.buyTrade)] = 0
            _self.buyAmount.loc[len(_self.buyAmount)] = (
                _self.buyTrade.iloc[-1] * _self.Strategy.Data.data.loc[i, "close"]
            )  # 买入金额更新

            ## =======卖出控制======
            selltrade = fixed_position * 100
            if _self.position.iloc[i - 1] == 0:  # 持仓=0
                _self.sellTrade.loc[len(_self.sellTrade)] = 0
            elif _self.Strategy.sellSignal.iloc[i] == True:  # 有卖出信号
                if (  # 股价增长6%
                    abs(
                        (_self.Strategy.Data.data.loc[i - 1, "close"] - last_buy)
                        / last_buy
                    )
                    > 0.06
                ):
                    _self.sellTrade.loc[len(_self.sellTrade)] = (
                        selltrade
                        if selltrade <= _self.position.iloc[-1]
                        else _self.position.iloc[-1]
                    )  # 卖出量是上一时刻钱包余额的1%,向下取100的整数

                else:  # 股价增长不到6%不卖
                    _self.sellTrade.loc[len(_self.sellTrade)] = 0
                    # print("拒绝卖出！没有浮盈。你可能错过了买入机会。\nindex：", i,
                    #     "\n时间：",_self.Strategy.Data.data.loc[i,'time'],
                    #     '\n预备卖出x股:',selltrade,
                    #     "\n预备卖出价：",_self.Strategy.Data.data.loc[i,'close'],
                    #     "\n成本价:",_self.Strategy.Data.data.loc[i-1,'Hold_Amount']/_self.Strategy.Data.data.loc[i-1,'Hold'],
                    #     "\n"
                    # )
                # print("拒绝卖出！没有持仓。你可能错过了盈利机会。\nindex：", i,
                #         "\n时间：",_self.Strategy.Data.data.loc[i,'time'],
                #         "\n(昨日)钱包余额:",_self.Strategy.Data.data.loc[i - 1, "Balance"],
                #         '\n(昨日)持仓金额:',_self.Strategy.Data.data.loc[i - 1, "Hold_Amount"],
                #         "\n卖出价：",_self.Strategy.Data.data.loc[i,'close'],
                #         "\n成本价:",_self.Strategy.Data.data.loc[i-1,'Hold_Amount']/_self.Strategy.Data.data.loc[i-1,'Hold'],
                #         "\n"
                #     )
            else:  # 没有卖出信号
                if (  # 资金占用时间超过5天 或 已跌4%)，必须平仓
                    i - last_buy_index >= 12 * 4 * 5
                ) | (
                    (_self.Strategy.Data.data.loc[i - 1, "close"] - last_buy) / last_buy
                    < -0.04
                ):
                    _self.sellTrade.loc[len(_self.sellTrade)] = (
                        selltrade
                        if selltrade <= _self.position.iloc[-1]
                        else _self.position.iloc[-1]
                    )
                    # print("时间超过x个交易日,强制平仓！。\nindex：", i,
                    #     "\n时间：",_self.Strategy.Data.data.loc[i,'time'],
                    #     "\n(昨日)钱包余额:",_self.Strategy.Data.data.loc[i - 1, "Balance"],
                    #     '\n(昨日)持仓金额:',_self.Strategy.Data.data.loc[i - 1, "Hold_Amount"],
                    #     "\n卖出价：",_self.Strategy.Data.data.loc[i,'close'],
                    #     "\n成本价:",_self.Strategy.Data.data.loc[i-1,'Hold_Amount']/_self.Strategy.Data.data.loc[i-1,'Hold'],
                    #     "\n"
                    # )
                else:  # 资金占用时间没有超过3天 且 没有跌3%，不卖
                    _self.sellTrade.loc[len(_self.sellTrade)] = 0

            _self.sellAmount.loc[len(_self.sellAmount)] = (
                _self.sellTrade.iloc[-1] * _self.Strategy.Data.data.loc[i - 1, "close"]
            )  # 卖出金额更新

            # 钱包余额变化
            Balance_Change = -_self.buyAmount.iloc[-1] + _self.sellAmount.iloc[-1]
            # 更新钱包余额
            _self.balance.loc[len(_self.balance)] = (
                _self.balance.iloc[-1] + Balance_Change
            )

            # 更新持仓数
            _self.position.loc[len(_self.position)] = (
                _self.position.iloc[-1]
                + _self.buyTrade.iloc[-1]
                - _self.sellTrade.iloc[-1]
            )
            # 更新持仓金额
            _self.positionAmount = (
                _self.position * _self.Strategy.Data.data.loc[i - 1, "close"]
            )

        return _self
        # # 检查是否有错过的机会
        # missed_buy = (self.Strategy.Data.data["Buy_Signal"] == 1) & (self.Strategy.Data.data["BuyTrade"] == 0)
        # missed_sell = (self.Strategy.Data.data["Sell_Signal"] == 1) & (self.Strategy.Data.data["SellTrade"] == 0)
        # if missed_buy.any():
        #     print("You missed a chance to buy on the following indices:", missed_buy[missed_buy].index.tolist())
        # if missed_sell.any():
        #     print("You missed a chance to sell on the following indices:", missed_sell[missed_sell].index.tolist())

    @st.cache_resource
    def pairTrade_fixed_position(_self):
        """
        买入量 = 卖出量 = 资金可购买股数/100
        更新buy,sell,position
        """
        # _self.Strategy.Data.data.loc[:,'close'] = _self.Strategy.Data.data.loc[:,'close'].astype(float)

        # 计算1%加仓仓位
        fixed_position = int(
            int(_self.balance_init / _self.Strategy.Data.data.loc[0, "close"] / 100)
            / 100
        )  # 1代表100股

        # 记录上次买卖价格
        last_buy = []
        last_buy_index = 0

        # 对于时刻i，如果有signal，signal是否用了i时数据？——不该用
        for i in tqdm(
            range(1, len(_self.Strategy.Data.data)),
            desc="进度条",
            unit="%",
            leave=False,
        ):

            # 计算买入量buytrade -----先写一个简单的买入卖出
            buytrade = fixed_position * 100  # 买入股数
            if (_self.Strategy.buySignal.iloc[i] == True) and (
                (
                    (last_buy is not None)
                    and (
                        (_self.Strategy.Data.data.loc[i - 1, "close"] - last_buy[-1])
                        / last_buy[-1]
                        < -0.03
                    )
                )
            ):
                _self.buyTrade.loc[len(_self.buyTrade)] = buytrade
                last_buy.append(_self.Strategy.Data.data.loc[i - 1, "close"])
            else:
                _self.buyTrade.loc[len(_self.buyTrade)] = 0

            _self.buyAmount.loc[len(_self.buyAmount)] = (
                _self.buyTrade.iloc[-1] * _self.Strategy.Data.data.loc[i, "close"]
            )  # 买入金额更新

            ## =======卖出控制======
            selltrade = fixed_position * 100
            if _self.position.iloc[i - 1] == 0:  # 持仓=0
                _self.sellTrade.loc[len(_self.sellTrade)] = 0
            elif _self.Strategy.sellSignal.iloc[i] == True:  # 有卖出信号
                if (  # 股价增长6%
                    _self.Strategy.Data.data.loc[i - 1, "close"] - last_buy[0]
                ) / last_buy[0] > 0.06:
                    _self.sellTrade.loc[len(_self.sellTrade)] = (
                        selltrade
                        if selltrade <= _self.position.iloc[-1]
                        else _self.position.iloc[-1]
                    )  # 卖出量是上一时刻钱包余额的1%,向下取100的整数

                else:  # 股价增长不到6%不卖
                    _self.sellTrade.loc[len(_self.sellTrade)] = 0
            else:  # 没有卖出信号
                if (  # 资金占用时间超过10天 或 已跌6%)，必须平仓
                    i - last_buy_index >= 12 * 4 * 5
                ) | (
                    (_self.Strategy.Data.data.loc[i - 1, "close"] - last_buy[0])
                    / last_buy[0]
                    < -0.06
                ):
                    _self.sellTrade.loc[len(_self.sellTrade)] = (
                        selltrade
                        if selltrade <= _self.position.iloc[-1]
                        else _self.position.iloc[-1]
                    )
                else:  # 资金占用时间没有超过3天 且 没有跌6%，不卖
                    _self.sellTrade.loc[len(_self.sellTrade)] = 0

            _self.sellAmount.loc[len(_self.sellAmount)] = (
                _self.sellTrade.iloc[-1] * _self.Strategy.Data.data.loc[i - 1, "close"]
            )  # 卖出金额更新

            # 钱包余额变化
            Balance_Change = -_self.buyAmount.iloc[-1] + _self.sellAmount.iloc[-1]
            # 更新钱包余额
            _self.balance.loc[len(_self.balance)] = (
                _self.balance.iloc[-1] + Balance_Change
            )

            # 更新持仓数
            _self.position.loc[len(_self.position)] = (
                _self.position.iloc[-1]
                + _self.buyTrade.iloc[-1]
                - _self.sellTrade.iloc[-1]
            )
            # 更新持仓金额
            _self.positionAmount = (
                _self.position * _self.Strategy.Data.data.loc[i - 1, "close"]
            )

        return _self

    @st.cache_resource
    def conditionTrade_fixed_position(_self):
        """
        买入量 = 卖出量 = 资金可购买股数/100
        更新buy,sell,position

        第i天
        buySignal.iloc[i]  信号已经向后shift过,所以是i,i-1,i...的window
        第i天买不到第i天的价格，所以实际上购买是发生在第i-1天的。但考虑高频后存在滑点，就以后一个window的收盘价作为买入，因此是第i天价格。
        last_buy =
        """
        # _self.Strategy.Data.data.loc[:,'close'] = _self.Strategy.Data.data.loc[:,'close'].astype(float)

        # 计算1%加仓仓位
        fixed_position = int(
            int(_self.balance_init / _self.Strategy.Data.data.loc[0, "close"] / 100) / 2
        )  # 1代表100股

        # 记录上次买卖价格
        last_buy = None
        last_buy_index = 0
        # 对于时刻i，如果有signal，signal是否用了i时数据？——不该用
        _self.Strategy.Data.data.loc[:, "date"] = pd.to_datetime(_self.Strategy.Data.data["date"])

        for i in tqdm(
            range(1, len(_self.Strategy.Data.data)),
            desc="进度条",
            unit="%",
            leave=False,
        ):

            # 计算买入量buytrade -----先写一个简单的买入卖出
            buytrade = fixed_position * 100  # 买入股数

            # ========买入控制========
            # 有买入信号
            # 未买入
            if (_self.Strategy.buySignal.iloc[i] == True) and (last_buy is None):
                _self.buyTrade.loc[len(_self.buyTrade)] = buytrade
                last_buy = _self.Strategy.Data.data.loc[i, "close"]
                last_buy_index = i
            else:
                _self.buyTrade.loc[len(_self.buyTrade)] = 0

            _self.buyAmount.loc[len(_self.buyAmount)] = (
                _self.buyTrade.iloc[-1] * _self.Strategy.Data.data.loc[i, "close"]
            )  # 买入金额更新

            # print(i) # debug
            # print(len(_self.buyAmount))

            # ========卖出控制========
            selltrade = fixed_position * 100
            # print("#"*20)
            # print(type(_self.Strategy.Data.data.loc[last_buy_index, 'time'])) #debug
            # print(type(_self.Strategy.Data.data.loc[last_buy_index, 'date'])) #debug

            # print(_self.Strategy.Data.data.loc[last_buy_index, 'time']) #debug
            # print(_self.Strategy.Data.data.loc[last_buy_index, 'date']) #debug

            # print(type(_self.Strategy.Data.data.index[last_buy_index])) #debug
            # 未买入 | 买入时间还在当天  -> 不卖
            if (last_buy is None) | (
                (last_buy is not None)
                & (
                    _self.Strategy.Data.data.loc[last_buy_index, "date"].strftime(
                        "%Y-%m-%d"
                    )
                    == _self.Strategy.Data.data.loc[i, "date"].strftime("%Y-%m-%d")
                )
            ):
                _self.sellTrade.loc[len(_self.sellTrade)] = 0
                _self.sellPrice.loc[len(_self.sellPrice)] = 0
            # (有卖出信号&保底盈利6%) | 买入时间占用5天 | 无条件止盈20% | 止损3% |
            elif (_self.Strategy.sellSignal.iloc[i] == True) & (
                _self.reach_limit(i, last_buy=last_buy, pct=0.09)[0]
            ):  # 超过保底盈利且有卖出信号
                #     _self.reach_limit(i,last_buy=last_buy,pct = 0.2)[0] # 无条件止盈
                # )|(
                _self.sellTrade.loc[len(_self.sellTrade)] = selltrade
                _self.sellPrice.loc[len(_self.sellPrice)] = _self.reach_limit(
                    i, last_buy=last_buy, pct=0.06
                )[2]
                last_buy = None
                # debug
            elif (_self.Strategy.sellSignal.iloc[i] == True) & (
                _self.reach_limit(i, last_buy=last_buy, pct=-0.03)[0]
            ):  # 止损
                _self.sellTrade.loc[len(_self.sellTrade)] = selltrade
                _self.sellPrice.loc[len(_self.sellPrice)] = _self.reach_limit(
                    i, last_buy=last_buy, pct=-0.03
                )[2]
                last_buy = None

            elif i - last_buy_index >= 12 * 4 * 15:  # 买入时间占用15天
                _self.sellTrade.loc[len(_self.sellTrade)] = selltrade
                _self.sellPrice.loc[len(_self.sellPrice)] = (
                    _self.Strategy.Data.data.loc[i, "close"]
                )
                last_buy = None

                # debug
                # if (_self.reach_limit(i,last_buy=last_buy,pct = 0.06)[0])&(_self.reach_limit(i,last_buy=last_buy,pct = 0.2)[0]):
                #     print("同时满足了两个条件！")
                # else:
                #     pass

            else:  # 有持仓，且没有卖出信号
                _self.sellTrade.loc[len(_self.sellTrade)] = 0
                _self.sellPrice.loc[len(_self.sellPrice)] = 0

            _self.sellAmount.loc[len(_self.sellAmount)] = (
                _self.sellTrade.iloc[-1] * _self.sellPrice.iloc[-1]
            )  # 卖出金额更新

            # 钱包余额变化
            Balance_Change = -_self.buyAmount.iloc[-1] + _self.sellAmount.iloc[-1]
            # 更新钱包余额
            _self.balance.loc[len(_self.balance)] = (
                _self.balance.iloc[-1] + Balance_Change
            )

            # 更新持仓数
            _self.position.loc[len(_self.position)] = (
                _self.position.iloc[-1]
                + _self.buyTrade.iloc[-1]
                - _self.sellTrade.iloc[-1]
            )
            # 更新持仓金额
            _self.positionAmount.loc[len(_self.positionAmount)] = (
                _self.position.iloc[-1] * _self.Strategy.Data.data.loc[i, "close"]
            )

            if i == 20:
                print(_self.profit_cum.iloc[-1])

            # if _self.position.iloc[-1]!=0:
            #     print(_self.position.iloc[-1]) # debug
        return _self

    def reach_limit(self, i, last_buy, pct):
        """
        计算止盈线,如果触发止盈线，返回[是否触发止盈，止盈线价格，止盈价格]
        """

        if last_buy == None:
            pass
        else:
            limit = last_buy * (1 + pct)  # 保底止盈0.06
            a = self.Strategy.Data.data.loc[i, "high"]
            b = self.Strategy.Data.data.loc[i, "low"]

            if (b <= limit) and (limit <= a):  # 含盖止盈线
                return [True, limit, limit]
            elif pct < 0:
                if limit < b:  # 高开未触发止损线
                    return [False, limit, "未触发止损"]
                else:  # 低开触发止损
                    return [True, limit, self.Strategy.Data.data.loc[i, "open"]]
            else:
                if limit < b:  # 高开超过止盈线
                    return [True, limit, self.Strategy.Data.data.loc[i, "open"]]
                else:  # 未触发保底止盈
                    return [False, limit, "未触发止盈"]

    # 收益计算
    def backtest(self):
        """
        基于买入量和卖出量,计算股票交易的收益和风险指标。

        更新profit,cose,
        参数:
        self.Strategy.Data.data (DataFrame): 包含交易数据的DataFrame，应包括'BuyTrade', 'SellTrade', 'close'等列。
        字段含义：
        Profit：累计收益
        Return：累计净收益率 --- 小数

        """
        # self.fixed_position()
        # self.pairTrade_fixed_position()
        self.conditionTrade_fixed_position()

        # 计算成本?
        self.cost = self.buyAmount.cumsum() - self.sellAmount.cumsum()  # 总买入金额

        # 计算总资产
        self.asset = self.balance + self.positionAmount  # 余额+持仓

        # 计算累计净收益 截止当前收益净值  =子弹+仓-初始
        self.profit_cum = self.asset - self.balance_init

        # 计算资产变动
        self.profit_change = self.profit_cum.diff()

        # 计算 累计净收益的收益率
        self.roi = self.profit_cum / self.balance_init  # 收益的百分比变化
        # self.Strategy.Data.data.loc[self.Strategy.Data.data["Timely_Return"].isna(), "Timely_Return"] = 0
        self.roi_pct = self.profit_cum.pct_change()  #
        #########

        # 计算年化平均回报率
        annualized_return = (self.asset.iloc[-1] / self.balance_init) ** (
            self.tradeDay / len(self.Strategy.Data.data)
        ) - 1

        # 计算年化波动率？ (年化平均回报率的标准差)*sqrt(交易日)
        annualized_volatility = np.nanstd(self.roi_pct) * np.sqrt(
            self.tradeDay / len(self.Strategy.Data.data)
        )

        # 计算Sharpe比率？ (年化平均回报率-无风险利率)/波动率
        sharpe_ratio = (annualized_return - self.risk_free_rate) / annualized_volatility

        # 计算回撤（这里需要先计算累计收益）
        self.profit_max = self.profit_cum.cummax()  # 最高收益t
        self.drawdown = self.profit_cum - self.profit_max  # 回撤t
        self.drawdown_max = self.drawdown.cummin()  # 最大回撤t
        self.drawdown_pct = self.drawdown / self.drawdown_max  # 回撤率t (+)

        max_drawdown = self.drawdown_max.min()  # 历史最大回撤
        max_drawdown_pct = self.drawdown_pct.max()  # 历史最大回撤率 (+)
        cumulative_max = self.profit_max.max()  # 历史最大收益

        # print(np.std(self.roi_pct))
        # 打印收益指标信息
        names = [
            "无风险利率",
            "交易日",
            "年化平均回报率",
            "年化波动率",
            "Sharpe Ratio",
            "最大回撤",
            "最大回撤率",
            "历史最大收益",
        ]
        columns = [
            self.risk_free_rate,
            self.tradeDay,
            annualized_return,
            annualized_volatility,
            sharpe_ratio,
            max_drawdown,
            max_drawdown_pct,
            cumulative_max,
        ]

        is_pct = [1, 0, 1, 1, 0, 0, 1, 0]

        for name, column, pct in zip(names, columns, is_pct):
            if pct == 1:
                st.text(f"{name}: {column:.2%}")
            else:
                st.text(f"{name}: {column}")

        fig = go.Figure()
        # =============累计收益曲线、持仓曲线===========
        yparas = [self.profit_cum, self.positionAmount]
        colors = ["red", "blue"]
        names = ["net_profit_cum", "positionAmount"]
        for y, color, name in zip(yparas, colors, names):
            fig.add_trace(
                go.Scatter(
                    x=self.Strategy.Data.data.index,
                    y=y,
                    yaxis="y1",
                    mode="lines",
                    line=dict(width=0.8, color=color),
                    showlegend=True,
                    name=name,
                )
            )

        # 收益率曲线
        # fig.add_trace(
        #     go.Scatter(
        #         x=self.Strategy.Data.data.index,
        #         y=self.roi * 100,
        #         yaxis="y2",
        #         mode="lines",
        #         line=dict(width=1.5, color="yellow"),
        #         showlegend=True,
        #         name="ROI(%)",
        #         hovertext=self.Strategy.Data.data["time"],
        #     )
        # )
        fig.add_hline(
            y=0,
            yref="y1",
            line_dash="dash",
            line_color="white",
            annotation_text="y=0",
            annotation_position="top left",
        )

        fig.update_layout(
            title="累计收益曲线",
            xaxis=dict(
                title="时间",
                tickvals=self.Strategy.Data.data.index[::1000],  # 用于定位的值
                ticktext=self.Strategy.Data.data["time"][:-10][
                    ::1000
                ],  # 想要显示在 x 轴上的值
                tickangle=45,  # 如果时间标签很长，可以旋转以便阅读
            ),
            yaxis=dict(
                title="Profit",  # 左侧 y 轴标题
                # titlefont=dict(color="purple"),  # 左侧 y 轴字体颜色
                # tickfont=dict(color="blue"),  # 左侧 y 轴刻度颜色
                fixedrange=True,
                range=[-500000, 1000000],
            ),
            # yaxis2=dict(
            #     title="return_pct",  # 右侧 y 轴标题
            #     # titlefont=dict(color="orange"),  # 右侧 y 轴字体颜色
            #     # tickfont=dict(color="orange"),  # 右侧 y 轴刻度颜色
            #     overlaying="y",  # 将右侧 y 轴叠加在左侧 y 轴
            #     side="right",  # 将右侧 y 轴显示在右边
            # ),
            template="plotly",
            legend=dict(x=0.1, y=1.1),  # 设置图例位置
            hovermode="x unified",
        )
        st.title("收益")
        st.plotly_chart(fig)

    def get_data(self):

        # st.title("策略点")
        # strategy = pd.DataFrame(
        #     {
        #         "time": self.Strategy.Data.data["time"],
        #         "buyAmount": self.buyAmount,
        #         "buyTrade": self.buyTrade,
        #         "sellAmount": self.sellAmount,
        #         "sellTrade": self.sellTrade,
        #         "position": self.position,
        #         "positionAmount": self.positionAmount,
        #         "balance": self.balance,
        #         "asset": self.asset,
        #         "profit_cum": self.profit_cum,
        #     }
        # )

        st.title("交易信息")
        # st.write(
        #     len(self.Strategy.Data.data["time"]),
        #     len(self.buyAmount.tolist()),
        #     len(self.sellAmount.tolist()),
        #     len(self.balance.tolist()),
        #     len(self.profit_cum.tolist())
        # )
        # st.write(
        #     self.buyAmount[self.buyAmount.isna()]
        # )
        # st.write(
        #     self.sellAmount[self.sellAmount.isna()]
        # )
        # st.write(
        #     self.balance[self.balance.isna()]
        # )
        # st.write(
        #     self.profit_cum[self.profit_cum.isna()]
        # )

        test = pd.DataFrame(
            {
                "time": self.Strategy.Data.data["time"],
                "close": self.Strategy.Data.data["close"],
                "sellprice": self.sellPrice,
                "buyAmount": self.buyAmount,
                "sellAmount": self.sellAmount,
                "positionAmount": self.positionAmount,
                "balance": self.balance,
                "asset": self.asset,
                "profit_cum": self.profit_cum,
                "profit_change": self.profit_change,
                "buyTrade": self.buyTrade,
                "sellTrade": self.sellTrade,
                "position": self.position,
            }
        ).reset_index(drop=True)
        order = test[(test["buyTrade"] != 0) | (test["sellTrade"] != 0)]
        st.write(order)
        st.write(f"胜率:{order[order['profit_change']>0].shape[0]/order.shape[0]}")
        st.write(f"败率:{order[order['profit_change']<0].shape[0]/order.shape[0]}")
        
        win = order.loc[order['profit_change']>0,'profit_change'].sum()
        loss  = order.loc[order['profit_change']<0,'profit_change'].sum()
        st.write(
            f"盈亏比:{win/loss}"
        )


class Drawer:

    def __init__(self, backtest):

        self.default_line_width = 0.8
        self.fig = go.Figure()
        self.Strategy: Strategy = backtest.Strategy
        self.Data: Data = backtest.Data
        self.BackTesting: BackTesting = backtest

    def plot_boxplot(self, indices, columns):
        """
        使用seaborn绘制指定行索引和列名的箱线图

        参数:
            indices: 行索引列表
            columns: 列名列表
        """
        data_subset = self.data.loc[indices, columns]
        sns.boxplot(data=data_subset)

    def saveChart(self, fig, filename):
        """
        保存图表为HTML文件
        :param fig: plotly图表对象
        :param filename: 保存文件名
        """
        fig.write_html(f"charts/{filename}.html")

    def drawClose(self, color):
        """
        绘制移动平均线
        :param data: 包含价格数据的DataFrame
        :param n: 移动平均窗口列表
        """
        print("#"*20)
        # print("drawclose")
        # print(type(self.Data.data["time"].iloc[20]))
        # print(self.Data.data["time"].dtype)
        # mask = self.Data.data["time"].apply(lambda x: not isinstance(x, pd.Timestamp))
        # print(self.Data.data.loc[mask, "time"])

        self.fig.add_trace(
            go.Scatter(
                x=self.Data.data.index,
                y=self.Data.data["close"],
                name="Close",
                mode="lines",
                line=dict(color=color, width=self.default_line_width),
                # hovertext = self.Data.data["time"].dt.strftime("%Y-%m-%d %H:%M"),
                hovertext = self.Data.data["time"],
            )
        )

    def drawCandle(self):
        """
        绘制移动平均线
        :param data: 包含价格数据的DataFrame
        :param n: 移动平均窗口列表
        """

        self.fig.add_trace(
            go.Candlestick(
                x=self.Data.data.index,
                close=self.Data.data["close"],
                open=self.Data.data["open"],
                low=self.Data.data["low"],
                high=self.Data.data["high"],
                name="Price",
                # mode="lines",
                # line=dict(color=color, width=self.default_line_width),
                hovertext=self.Data.data["time"].dt.strftime("%Y-%m-%d %H:%M"),
            )
        )
    def drawLoss(self):
        self.fig.add_trace(
            go.Candlestick(
                x=self.Data.data.index,
                close=self.Data.data["close"],
                open=self.Data.data["open"],
                low=self.Data.data["low"],
                high=self.Data.data["high"],
                name="Price",
                # mode="lines",
                # line=dict(color=color, width=self.default_line_width),
                hovertext=self.Data.data["time"].dt.strftime("%Y-%m-%d %H:%M"),
            )
        )


    def drawMA(self, n, color):
        """
        绘制移动平均线
        :param data: 包含价格数据的DataFrame
        :param n: 移动平均窗口列表
        """

        self.fig.add_trace(
            go.Scatter(
                x=self.Data.data.index,
                y=self.Data.get_sma(n),
                name=f"SMA_{n}",
                line=dict(color=color, width=self.default_line_width),
            )
        )

    def drawRSI(self, n, color):
        """
        绘制移动平均线
        :param data: 包含价格数据的DataFrame
        :param n: 移动平均窗口列表
        """

        self.fig.add_trace(
            go.Scatter(
                x=self.Data.data.index,
                y=self.Data.get_rsi(n) * self.Data.data["close"].iloc[100] / 300,
                name=f"RSI_{n}",
                line=dict(color=color, width=self.default_line_width),
            )
        )

    def drawMACD(self, short_window, signal_window, long_window, color):
        """
        绘制移动平均线
        :param data: 包含价格数据的DataFrame
        :param n: 移动平均窗口列表
        """

        self.fig.add_trace(
            go.Scatter(
                x=self.Data.data.index,
                y=self.Data.get_macd(short_window, signal_window, long_window),
                name=f"MACD_{short_window}_{signal_window}_{long_window}",
                line=dict(color=color, width=self.default_line_width),
            )
        )

    def drawBS(self):
        """
        绘制移动平均线
        :param data: 包含价格数据的DataFrame
        :param n: 移动平均窗口列表
        """
        self.drawClose("white")
        # self.drawCandle()
        buypoint = self.BackTesting.buyTrade[self.BackTesting.buyTrade != 0].index
        # print("="*20) # debug
        # print(type(self.Data.data["time"]))
        # print(type(self.Data.data["time"].iloc[7]))
        sellpoint = self.BackTesting.sellTrade[self.BackTesting.sellTrade != 0].index
        BSpoint = [buypoint, sellpoint]
        colors = ["blue", "red"]
        for BS, color in zip(BSpoint, colors):
            self.fig.add_trace(
                go.Scatter(
                    x=BS,
                    marker=dict(size=5.1),
                    y=self.Data.data.loc[BS, "close"],
                    yaxis="y1",
                    mode="markers",
                    name=f"{self.Strategy.name}BSpoint",
                    marker_color=color,
                )
            )

    def draw(self):
        # 更新布局
        self.fig.update_layout(
            xaxis=dict(
                title="时间",
                tickvals=self.Data.data.index[::2000],  # 用于定位的值
                ticktext=self.Data.data["time"].dt.strftime("%Y-%m-%d %H:%M")[
                    ::2000
                ],  # 想要显示在 x 轴上的值
                tickangle=45,  # 如果时间标签很长，可以旋转以便阅读
            ),
            title="移动平均线",
            yaxis=dict(
                title="MA",  # y 轴标题
                tickfont=dict(color="white"),  # y 轴刻度颜色
            ),
            template="plotly",  #
            legend=dict(x=0.1, y=1.1),  # 图例位置
            hovermode="x unified",  # 悬浮显示信息
            # bargap=0.3,  # 调整柱状图之间的间距
        )
        st.write(self.fig)

    def drawHover(self, indicator):
        self.fig.add_trace(
            go.Scatter(
                # x=data["time"],
                x=self.Data.data.index,
                y=1,
                yaxis="y1",
                mode="lines",
                line=dict(width=0, color="white"),
                showlegend=False,
                hovertext=self.Data.data["RSI"].apply(
                    lambda x: f"720RSI Ratio: {x:.2f}"
                ),
                hoverinfo="text",
            )
        )

    def clean_fig(self):
        self.fig.data = []
