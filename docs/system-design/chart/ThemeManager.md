# ThemeManager 类设计文档

## 功能职责
- 专注于主题管理（颜色预设/主题切换）
- 提供主题切换功能
- 作为颜色配置的单一数据源
- ThemeManager 服务多个模块（如图表/报表/仪表盘）

## 属性
```python
presets: Dict[str, Dict[str, str]]
```
- 存储不同主题的颜色配置
- 键为预设名称，值为颜色配置字典
- 默认包含"default"和"dark"主题

## 关键方法
### `get_colors(preset_name: str = "default") -> Dict[str, str]`
- 获取指定主题的颜色配置
- 参数：preset_name - 主题名称（默认为"default"）
- 返回：颜色配置字典
- 如果请求的主题不存在，返回默认主题配置

### 示例配置
```python
{
    "default": {
        "up_color": "#25A776",
        "down_color": "#EF4444",
        "primary": "#2c7be5",
        "secondary": "#6c757d",
        "background": "#1E1E1E"
    },
    "dark": {
        "up_color": "#3D9970",
        "down_color": "#FF4136",
        "primary": "#0074D9",
        "secondary": "#5a6268",
        "background": "#121212"
    }
}

## 改进方向
在 ThemeManager 中增加主题注册机制，支持动态扩展
