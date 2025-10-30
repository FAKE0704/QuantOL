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
             fast: int = 12, slow: int = 26, signal: int = 9) -> float:
        """计算MACD（当前索引值）"""
        if current_index < max(fast, slow, signal):
            return 0.0  # 数据不足时返回安全值
            
        sub_series = series.iloc[:current_index+1].astype(float)
        ema_fast = sub_series.ewm(span=fast).mean().iloc[-1]
        ema_slow = sub_series.ewm(span=slow).mean().iloc[-1]
        macd_line = ema_fast - ema_slow
        
        # 计算信号线需要更多数据
        if current_index < max(fast, slow) + signal - 1:
            return macd_line
            
        macd_series = sub_series.ewm(span=fast).mean() - sub_series.ewm(span=slow).mean()
        signal_line = macd_series.ewm(span=signal).mean().iloc[-1]
        return macd_line - signal_line
