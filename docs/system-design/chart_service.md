# 图表服务系统设计文档

## 核心类

### DataBundle 数据容器类
- **功能**：统一存储和管理多种类型的金融数据
- **主要属性**：
  - `kline_data`: K线数据(DataFrame)
  - `trade_records`: 交易记录数据(DataFrame) 
  - `capital_flow`: 资金流数据(DataFrame)
- **核心方法**：
  - `get_all_columns()`: 获取所有数据列名
  - `__init__()`: 初始化数据容器

### ChartService 图表服务主类
- **功能**：提供图表创建、渲染和交互服务
- **主要属性**：
  - `data_bundle`: 关联的数据容器
  - `figure`: 当前图表对象
  - `_interaction_service`: 交互服务(惰性初始化)
- **核心方法**：
  - `create_kline()`: 创建K线图
  - `create_volume_chart()`: 创建成交量图
  - `create_capital_flow_chart()`: 创建资金流图
  - `create_combined_chart()`: 创建组合图表
  - `render_chart_controls()`: 渲染图表配置UI

### ChartBase 抽象基类
- **功能**：定义图表基类接口
- **抽象方法**：
  - `render()`: 必须实现的渲染方法
- **属性**：
  - `figure`: Plotly图表对象
  - `config`: 图表配置

## 主要图表实现类

### CandlestickChart K线图实现
- **特性**：
  - 支持均线叠加(MA5/MA10/MA20)
  - 自定义涨跌颜色
- **配置项**：
  - `add_ma`: 是否显示均线
  - `ma_periods`: 均线周期列表

### VolumeChart 成交量图实现
- **特性**：
  - 自动根据涨跌着色
  - 支持成交量均线
- **配置项**：
  - `default_up_color`: 上涨颜色
  - `default_down_color`: 下跌颜色

### CapitalFlowChart 资金流图实现
- **特性**：
  - 双Y轴设计(主力和北向资金)
  - 堆叠式柱状图
- **配置项**：
  - `main_color`: 主力资金颜色
  - `north_color`: 北向资金颜色

## 交互设计

### InteractionService 交互服务
- **功能**：处理图表间联动
- **核心机制**：
  - 订阅/发布模式
  - 防抖处理(500ms)
  - 递归深度限制(MAX_RECURSION_DEPTH=5)
- **主要方法**：
  - `subscribe()`: 订阅图表事件
  - `handle_zoom_event()`: 处理缩放事件
  - `sync_zooming()`: 同步多个图表缩放

## 使用示例

```python
# 初始化数据容器
data = DataBundle(raw_data=df)

# 创建图表服务实例
chart_service = ChartService(data)

# 生成K线图
kline = chart_service.create_kline()

# 生成成交量图(带交互)
volume = chart_service.create_volume_chart(auto_listen=True)

# 渲染到Streamlit
st.plotly_chart(kline)
st.plotly_chart(volume)
```

## 配置管理

通过`ChartConfigManager`类管理图表配置：
- 默认配置路径: `src/support/config/chart_config.json`
- 支持动态加载和保存配置
- 配置项包括：
  - 主题(颜色/字体)
  - 布局(类型/间距)
  - 数据(字段/别名)

## 性能优化

1. **惰性初始化**：交互服务按需创建
2. **缓存机制**：使用`st.cache_resource`缓存图表实例
3. **批量渲染**：支持组合图表减少渲染次数
4. **数据裁剪**：自动限制显示数据量
