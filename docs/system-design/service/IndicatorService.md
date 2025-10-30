# 位置：
`src/core/strategy/indicators.py`
# 职责：
- 向量化指标计算（返回完整序列）
- 缓存机制：使用LRU缓存存储常用指标序列
- 预计算机制：在策略初始化时计算所需指标序列

# class IndicatorService

# property
_cache : 基于参数哈希的缓存

# method
def sma(series: pd.Series, window: int) -> pd.Series
def rsi(series: pd.Series, period: int) -> pd.Series
def macd(series: pd.Series) -> pd.Series

- calculate_indicator ：统一指标计算入口