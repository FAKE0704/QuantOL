# 类 ChartFactory
图表工厂类，支持动态注册和创建图表实例。通过工厂模式解耦图表类型定义与实例化过程，便于扩展新的图表类型。


字段名称|数据类型|说明
-|-|-
_chart_types	|Dict[str, Type[ChartBase]]	|存储已注册的图表类型（键：图表类型标识符，值：对应的图表类）

# 关键操作接口
## 注册管理
▸ register_chart(chart_type: str, chart_class: Type[ChartBase])​
　→ 注册新的图表类型到工厂

　▪ ​校验规则​：若 chart_class 未继承 ChartBase，抛出 TypeError
　▪ ​示例​：
　　ChartFactory.register_chart("candlestick", CandlestickChart)

▸ get_registered_charts() -> List[str]​
　→ 返回所有已注册图表类型的标识符列表

　▪ ​输出示例​：["capital_flow", "candlestick", "volume"]

## 实例控制
▸ `create_chart(chart_type: str, config: ChartConfig)` -> ChartBase​
　→ 根据类型标识符和配置对象动态创建图表实例

　▪ ​校验规则​：若 chart_type 未注册，抛出 ValueError
　▪ ​参数说明​：
　　config：包含图表标题、轴标签、数据集等配置的对象（参考 ChartConfig 结构）
　▪ ​返回​：初始化后的图表实例（如 CandlestickChart(config)）