import streamlit as st
import plotly.graph_objects as go


class Drawer:
    def __init__(self, data: list):
        """初始化绘图工具"""
        self.default_line_width = 1
        self.color = "blue"
        self.data = data
        self.fig = go.Figure()

    def drawMACD(self, fast=12, slow=26, signal=9):
        """
        绘制MACD指标
        :param data: 包含价格数据的DataFrame
        :param fast: 快速EMA周期
        :param slow: 慢速EMA周期
        :param signal: 信号线周期
        """
        fig = go.Figure()

        # 计算MACD
        exp1 = data["close"].ewm(span=fast, adjust=False).mean()
        exp2 = data["close"].ewm(span=slow, adjust=False).mean()
        macd = exp1 - exp2
        signal_line = macd.ewm(span=signal, adjust=False).mean()
        histogram = macd - signal_line

        # 添加MACD线
        fig.add_trace(
            go.Scatter(
                x=data.index,
                y=macd,
                name="MACD",
                line=dict(color="blue", width=self.default_line_width),
            )
        )

        # 添加信号线
        fig.add_trace(
            go.Scatter(
                x=data.index,
                y=signal_line,
                name="Signal",
                line=dict(color="orange", width=self.default_line_width),
            )
        )

        # 添加柱状图
        fig.add_trace(
            go.Bar(
                x=data.index,
                y=histogram,
                name="Histogram",
                marker_color=np.where(histogram >= 0, "green", "red"),
            )
        )

        # 更新布局
        fig.update_layout(
            title="MACD", xaxis_title="时间", yaxis_title="MACD", template="plotly_dark"
        )

        st.plotly_chart(fig)

    def drawBollingerBands(self, data, window=20, num_std=2):
        """
        绘制布林带
        :param data: 包含价格数据的DataFrame
        :param window: 移动平均窗口
        :param num_std: 标准差倍数
        """
        fig = go.Figure()

        # 计算布林带
        rolling_mean = data["close"].rolling(window=window).mean()
        rolling_std = data["close"].rolling(window=window).std()
        upper_band = rolling_mean + (rolling_std * num_std)
        lower_band = rolling_mean - (rolling_std * num_std)

        # 添加价格线
        fig.add_trace(
            go.Scatter(
                x=data.index,
                y=data["close"],
                name="价格",
                line=dict(color="white", width=self.default_line_width),
            )
        )

        # 添加布林带
        fig.add_trace(
            go.Scatter(
                x=data.index,
                y=upper_band,
                name="上轨",
                line=dict(color="red", width=self.default_line_width),
            )
        )

        fig.add_trace(
            go.Scatter(
                x=data.index,
                y=rolling_mean,
                name="中轨",
                line=dict(color="blue", width=self.default_line_width),
            )
        )

        fig.add_trace(
            go.Scatter(
                x=data.index,
                y=lower_band,
                name="下轨",
                line=dict(color="green", width=self.default_line_width),
            )
        )

        # 更新布局
        fig.update_layout(
            title="布林带",
            xaxis_title="时间",
            yaxis_title="价格",
            template="plotly_dark",
        )

        st.plotly_chart(fig)

    

    def drawVolume(self, data):
        """
        绘制成交量图
        :param data: 包含价格和成交量数据的DataFrame
        """
        fig = go.Figure()

        # 添加成交量柱状图
        fig.add_trace(
            go.Bar(
                x=data.index,
                y=data["volume"],
                name="成交量",
                marker_color=np.where(data["close"] >= data["open"], "green", "red"),
            )
        )

        # 更新布局
        fig.update_layout(
            title="成交量",
            xaxis_title="时间",
            yaxis_title="成交量",
            template="plotly_dark",
        )

        st.plotly_chart(fig)

    def drawCandlestick(self, data):
        """
        绘制K线图
        :param data: 包含开盘、收盘、最高、最低价格数据的DataFrame
        """
        fig = go.Figure()

        # 添加K线图
        fig.add_trace(
            go.Candlestick(
                x=data.index,
                open=data["open"],
                high=data["high"],
                low=data["low"],
                close=data["close"],
                name="K线",
            )
        )

        # 更新布局
        fig.update_layout(
            title="K线图",
            xaxis_title="时间",
            yaxis_title="价格",
            template="plotly_dark",
        )

        st.plotly_chart(fig)

    
    def drawRSI(self, data, window=14):
        """
        绘制相对强弱指数(RSI)
        :param data: 包含价格数据的DataFrame
        :param window: RSI计算窗口
        """
        fig = go.Figure()

        # 计算RSI
        delta = data["close"].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))

        # 添加RSI线
        fig.add_trace(
            go.Scatter(
                x=data.index,
                y=rsi,
                name="RSI",
                line=dict(color="blue", width=self.default_line_width),
            )
        )

        # 添加参考线
        fig.add_hline(y=30, line_dash="dash", line_color="red")
        fig.add_hline(y=70, line_dash="dash", line_color="red")

        # 更新布局
        fig.update_layout(
            title="相对强弱指数(RSI)",
            xaxis_title="时间",
            yaxis_title="RSI",
            template="plotly_dark",
        )

        st.plotly_chart(fig)


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
            showlegend=True,
        )
    )

    fig_rsi.add_hline(
        y=30,
        line_dash="dash",
        line_color="white",
        annotation_text="y=30",
        annotation_position="top left",
    )

    fig_rsi.add_hline(
        y=70,
        line_dash="dash",
        line_color="white",
        annotation_text="y=70",
        annotation_position="top left",
    )

    fig_rsi.update_layout(
        title=f"{window}RSI",
        xaxis=dict(
            gridcolor="white",
            title="时间",
            tickvals=data.index[::1000],
            ticktext=data["time"][::1000],
        ),
        yaxis=dict(
            gridcolor="white",
            title=f"{window}RSI",
            titlefont=dict(color="white"),
            tickfont=dict(color="white"),
            tickvals=[30, 70],
            ticktext=["30", "70"],
        ),
        template="plotly",
        legend=dict(x=0.1, y=1.1),  # 设置图例位置
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

    

