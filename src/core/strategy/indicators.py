"""指标计算服务（支持增量计算）"""
import pandas as pd
import numpy as np

class IndicatorService:
    """提供指标计算服务（支持增量计算）"""
    
    def __init__(self):
        self._cache = {}  # 基于参数哈希的缓存
    
    def calculate_indicator(self, func_name: str, series: pd.Series, 
                          current_index: int, *args) -> float:
        """统一指标计算入口
        Args:
            func_name: 指标函数名
            series: 输入序列（如收盘价）
            current_index: 当前索引位置
            *args: 指标函数参数
        Returns:
            当前索引位置的指标值
        """
        # 确保current_index是整数
        if not isinstance(current_index, int):
            current_index = int(current_index)
        # 边界检查
        if current_index < 0 or current_index >= len(series):
            raise IndexError(f"Invalid index {current_index} for series length {len(series)}")
        
        # 生成缓存键（避免缓存整个series）
        cache_key = (func_name, current_index, *args)
        
        # 检查缓存
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        # 统一转为小写进行函数路由
        func_name = func_name.lower()
        if func_name == 'sma':
            result = self._sma(series, current_index, *args)
        elif func_name == 'rsi':
            result = self._rsi(series, current_index, *args)
        elif func_name == 'macd':
            result = self._macd(series, current_index, *args)
        elif func_name == 'std':
            result = self._std(series, current_index, *args)
        elif func_name == 'zscore' or func_name == 'z_score':
            result = self._zscore(series, current_index, *args)
        elif func_name == 'ema':
            result = self._ema(series, current_index, *args)
        elif func_name == 'dif':
            result = self._dif(series, current_index, *args)
        elif func_name == 'dea':
            result = self._dea(series, current_index, *args)
        else:
            raise ValueError(f"Unsupported indicator: {func_name}")
        
        # 缓存结果
        self._cache[cache_key] = result
        return result

    def _sma(self, series: pd.Series, current_index: int, window: int) -> float:
        """计算简单移动平均（当前索引值）"""
        # 确保参数为整数
        current_index = int(current_index)
        window = int(window)
        
        # 验证索引范围
        if current_index < window - 1:
            return 0.0  # 数据不足时返回安全值
            
        # 计算切片索引并确保为整数
        start = int(current_index - window + 1)
        end = int(current_index + 1)
        
        # 执行切片计算
        return series.iloc[start:end].mean()

    def _rsi(self, series: pd.Series, current_index: int, period: int = 14) -> float:
        """计算相对强弱指数（当前索引值）"""
        # 确保period是整数
        period = int(period)
        if current_index < period:
            return 50.0  # RSI默认值
        
        sub_series = series.iloc[:current_index+1].astype(float)
        delta = sub_series.diff()
        gain = delta.where(delta > 0, 0.0)
        loss = -delta.where(delta < 0, 0.0)
        
        avg_gain = gain.rolling(period).mean().iloc[-1]
        avg_loss = loss.rolling(period).mean().iloc[-1]
        
        if avg_loss == 0:
            return 100.0 if avg_gain != 0 else 50.0
            
        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))

    def _macd(self, series: pd.Series, current_index: int,
             signal: int = 9, short: int = 12, long: int = 26) -> float:
        """计算MACD柱状图（当前索引值）
        MACD = 2 * (DIF - DEA)
        """
        current_index = int(current_index)
        signal = int(signal)
        short = int(short)
        long = int(long)

        # 计算DIF和DEA
        dif = self._dif(series, current_index, short, long)
        dea = self._dea(series, current_index, signal, short, long)

        # 如果DIF或DEA为0（数据不足），返回0
        if dif == 0.0 or dea == 0.0:
            return 0.0

        # MACD柱状图 = 2 * (DIF - DEA)
        return 2 * (dif - dea)

    def _dif(self, series: pd.Series, current_index: int, short: int, long: int) -> float:
        """计算DIF（快线移动平均 - 慢线移动平均）
        DIF = EMA(short) - EMA(long)
        """
        current_index = int(current_index)
        short = int(short)
        long = int(long)

        # 数据不足时返回安全值
        if current_index < long:
            return 0.0

        # 计算短期和长期EMA
        ema_short = self._ema(series, current_index, short)
        ema_long = self._ema(series, current_index, long)

        return ema_short - ema_long

    def _dea(self, series: pd.Series, current_index: int, signal: int, short: int, long: int) -> float:
        """计算DEA（DIF的移动平均）
        DEA = EMA(DIF, signal)
        """
        current_index = int(current_index)
        signal = int(signal)
        short = int(short)
        long = int(long)

        # 需要足够的数据来计算DIF，然后再对DIF计算EMA
        if current_index < long + signal:
            return 0.0

        # 计算DIF序列
        dif_series = []
        for i in range(long, current_index + 1):
            dif = self._dif(series, i, short, long)
            dif_series.append(dif)

        # 对DIF序列计算EMA
        dif_series_pd = pd.Series(dif_series)
        return dif_series_pd.ewm(span=signal, adjust=False).mean().iloc[-1]

    def _std(self, series: pd.Series, current_index: int, window: int) -> float:
        """计算标准差（当前索引值）"""
        current_index = int(current_index)
        window = int(window)

        # 数据不足时返回安全值
        if current_index < window - 1:
            return 0.0

        # 计算切片索引
        start = int(current_index - window + 1)
        end = int(current_index + 1)

        # 执行标准差计算（使用pandas的std方法，ddof=1表示样本标准差）
        return series.iloc[start:end].std(ddof=1)

    def _zscore(self, series: pd.Series, current_index: int, window: int) -> float:
        """计算Z分数（当前索引值）
        Z_SCORE = (current_value - SMA) / STD
        """
        current_index = int(current_index)
        window = int(window)

        # 数据不足时返回安全值
        if current_index < window:
            return 0.0

        # 计算SMA和STD
        sma = self._sma(series, current_index, window)
        std = self._std(series, current_index, window)

        # 避免除零
        if std == 0:
            return 0.0

        # 获取当前值
        current_value = series.iloc[current_index]

        # 计算Z分数
        return (current_value - sma) / std

    def _ema(self, series: pd.Series, current_index: int, window: int) -> float:
        """计算指数移动平均（当前索引值）
        EMA = (Current Price × Multiplier) + (Previous EMA × (1 - Multiplier))
        Multiplier = 2 / (window + 1)
        """
        current_index = int(current_index)
        window = int(window)

        # 数据不足时返回安全值
        if current_index < window - 1:
            return 0.0

        # 使用pandas的ewm方法计算EMA
        # span对应pandas中的中心质量衰减参数，alpha = 2/(span+1)
        sub_series = series.iloc[:current_index + 1].astype(float)
        return sub_series.ewm(span=window, adjust=False).mean().iloc[-1]
