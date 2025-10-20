# Streamlit 状态管理设计文档

## 概述

本文档定义了项目中 Streamlit 应用程序的状态管理原则和最佳实践，确保状态管理的一致性和可维护性。

## 核心设计原则

### 1. 状态管理集中化
- **原则**: 所有组件状态应通过 `st.session_state` 集中管理
- **实现**: 避免在组件中直接存储状态，所有状态变量都存储在 session_state 中

### 2. 避免直接操作
- **原则**: 不推荐在创建组件后直接修改其值
- **实现**: 组件创建后不通过 `st.session_state[key] = value` 方式修改已存在的 widget 值

### 3. 单一数据源
- **原则**: Session State 应是唯一的状态来源
- **实现**: 组件的值应完全依赖 session_state，避免混合使用默认值和 session_state

## 问题分析

### 当前问题
在策略配置页面的自定义规则编辑器中存在以下冲突：

```python
# strategy_config_ui.py:40 - 创建组件时设置默认值
st.session_state.get('buy_rule_default', '')

# rule_group_manager.py:130 - 通过 Session State API 直接设置值
self.session_state['buy_rule_default'] = group.get('buy_rule', '')
```

**错误信息**: `The widget with key "buy_rule_default" was created with a default value but also had its value set via the Session State API.`

### 根本原因
- Streamlit widget 不允许既通过 `value` 参数设置默认值，又通过 Session State API 设置值
- 这种双重赋值造成了状态管理冲突

## 解决方案

### 方案1: 仅使用 Session State（推荐）
```python
# 修改前
rule_group_manager.render_rule_editor_ui('buy_rule',
    st.session_state.get('buy_rule_default', ''), "default", 60)

# 修改后
rule_group_manager.render_rule_editor_ui('buy_rule', '', "default", 60)
# 组件值完全依赖 session_state['buy_rule_default']
```

### 方案2: 分离默认值存储
```python
# 使用不同的 key 存储默认值
self.session_state['buy_rule_default_value'] = group.get('buy_rule', '')
# 在 UI 初始化时使用，而不是在组件创建时
```

## 状态管理模式

### 初始化模式
```python
# 在页面或组件初始化时设置状态
if 'key' not in st.session_state:
    st.session_state['key'] = default_value
```

### 状态读取模式
```python
# 组件创建时不设置 value 参数，让 Streamlit 自动从 session_state 读取
st.text_area("标签", key="my_key")
```

### 状态更新模式
```python
# 通过用户交互或回调函数更新状态
def on_change():
    st.session_state['key'] = new_value

st.button("更新", on_click=on_change)
```

## 实施计划

### 阶段1: 修复当前问题
1. 修改 `strategy_config_ui.py` 移除默认值参数
2. 确保所有规则编辑器组件的状态管理一致性

### 阶段2: 全面审查
1. 审查所有组件的状态管理模式
2. 统一状态管理规范
3. 更新相关文档

### 阶段3: 建立规范
1. 制定状态管理编码规范
2. 添加代码审查检查点
3. 建立自动化测试

## 最佳实践

### DO（推荐做法）
- ✅ 在页面初始化时设置 session_state 默认值
- ✅ 使用 key 让组件自动从 session_state 读取值
- ✅ 通过回调函数更新状态
- ✅ 保持状态命名一致性

### DON'T（避免做法）
- ❌ 在创建组件时同时设置 value 和 key
- ❌ 直接通过 session_state 修改已创建的 widget 值
- ❌ 混合使用默认值和 session_state
- ❌ 在不同位置重复设置相同的状态

## 代码示例

### 正确的状态管理模式
```python
# 页面初始化
def initialize_page():
    if 'buy_rule' not in st.session_state:
        st.session_state['buy_rule'] = ''

# 组件创建
def render_rule_editor():
    st.text_area("加仓规则", key="buy_rule")

# 状态更新
def load_rule_group(group_name):
    group = get_rule_group(group_name)
    st.session_state['buy_rule'] = group.get('buy_rule', '')
```

### 错误的状态管理模式
```python
# ❌ 错误：混合使用默认值和 session_state
st.text_area("加仓规则",
    value=st.session_state.get('buy_rule', ''),
    key="buy_rule")

# ❌ 错误：直接修改已创建的 widget 值
st.session_state['buy_rule'] = "new_value"  # 在 widget 已创建后
```

## 结论

通过遵循这些原则和最佳实践，我们可以确保 Streamlit 应用程序的状态管理一致性、可维护性和可靠性。推荐使用方案1来解决当前的问题，并逐步应用到整个项目中。