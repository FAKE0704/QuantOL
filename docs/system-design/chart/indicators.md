
通过 IndicatorDecorator 装饰器应用到图表上

# 基类 Indicator


## IndicatorFactory


# 属性
_registry = {}  # 存储注册的指标类

# 方法
register
create

# 配置中心集成：
结合 ChartConfigManager 实现指标配置持久化


```python
# 应用到图表
decorated_chart = IndicatorDecorator(kline, indicators=indicators)
```

###
