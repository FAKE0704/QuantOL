# Streamlit 使用指南

## 安装与启动
```bash
pip install streamlit
streamlit run app.py
```

## 基本组件
1. 文本显示
```python
st.title("标题")
st.header("小标题")
st.text("普通文本")
```

2. 数据展示
```python
st.dataframe(df)  # 显示数据框
st.table(data)    # 静态表格
st.json(json)     # 显示JSON
```

3. 图表
```python
st.line_chart(data)
st.bar_chart(data)
st.pyplot(fig)    # Matplotlib图表
```

4. 交互组件
```python
st.button("按钮")
st.checkbox("复选框")
st.selectbox("选择框", options)
st.slider("滑块", min_value, max_value)
```

## 页面布局
1. 侧边栏
```python
with st.sidebar:
    st.title("侧边栏标题")
```

2. 分栏布局
```python
col1, col2 = st.columns(2)
with col1:
    # 第一列内容
with col2:
    # 第二列内容
```

## 状态管理
### st.session_state
`st.session_state`通过浏览器Cookie与服务器内存绑定，在用户会话期间（页面未刷新）保持数据持久性。每次脚本重跑（rerun）不会重置状态，但浏览器刷新或新标签页会创建新会话

Streamlit 的默认机制是：任何不在 `st.form` 内的组件交互都会立即触发全局 rerun


`st.expander` 的展开/折叠状态默认不会被自动保存到 session_state。当页面 rerun 时，该组件会恢复默认展开状态，导致其内部的控件被重新初始化
```python
# 初始化状态
if 'key' not in st.session_state:
    st.session_state['key'] = 'value'

selected = st.selectbox("选择城市", ["北京", "上海"], key="city_select")
# 等价于 st.session_state.city_select = selected


# 更新状态
st.session_state['key'] = 'new_value'
```

- 除了会话状态需要管理，还需要作显示内容的持久化

## 性能优化
1. 缓存数据
```python
@st.cache_data
def load_data():
    return pd.read_csv("data.csv")
```

2. 缓存计算
```python
@st.cache_resource
def expensive_computation():
    return result
```

## 部署
1. 本地运行
```bash
streamlit run app.py
```

2. 云部署
- Streamlit Cloud
- Docker容器
- 常规Web服务器
