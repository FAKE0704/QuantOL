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
```python
# 初始化状态
if 'key' not in st.session_state:
    st.session_state['key'] = 'value'

# 更新状态
st.session_state['key'] = 'new_value'
```

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
