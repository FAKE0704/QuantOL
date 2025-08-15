# 类 ChartConfigManager## 职责

ChartConfig类负责管理图表的所有配置项，包括：

- 主题配置（颜色、字体等）
- 布局配置（图表排列方式、高度比例等）
- 数据配置（显示字段、字段别名等） 作为配置中心，它统一管理图表呈现所需的各种参数。

## 属性

- `theme: ThemeConfig` - 主题配置对象
- `layout: LayoutConfig` - 布局配置对象
- `data: DataConfig` - 数据配置对象
- `_config_manager: ChartConfigManager` - 配置管理器实例

## 关键方法

### `__init__(self)`

初始化配置对象，创建默认的主题、布局和数据配置实例。
- ChartConfig 初始化时注入 ThemeManager 实例

### `load(self)`

从配置文件加载配置并更新当前配置对象：

1. 调用`_config_manager.load_config()`获取配置数据
2. 验证配置数据结构
3. 分别更新theme/layout/data配置

### `save(self)`

保存当前配置到文件：

1. 将theme/layout/data配置转换为字典
2. 调用`_config_manager.save_config()`保存

## 与ThemeManager的交互

ChartConfig通过ThemeManager获取主题配置：

- 在`load()`方法中，使用ThemeManager提供的方法获取主题配置
- 当用户通过UI更改主题时，ThemeManager会通知ChartConfig更新
- ChartConfig保存时会包含当前主题配置

## 示例代码

```python
# 初始化配置
config = ChartConfig()

# 加载配置
config.load()

# 使用配置
primary_color = config.theme.colors["primary"]

# 修改并保存配置
config.theme.mode = "dark"
config.save()
```
