import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
from typing import Optional
from services.theme_manager import ThemeManager
from datetime import datetime

async def show_global_market():
    # 初始化服务和数据库
    db = st.session_state.db
    
    # 页面标题
    st.title('全球市场资金分布')
    
    # 侧边栏控制面板
    with st.sidebar:
        st.header('控制面板')
        
        # 主题选择
        # theme = st.selectbox(
        #     "主题模式",
        #     options=list(theme_manager.themes.keys()),
        #     index=0
        # )
        
        # 时间范围选择
        date_range = st.date_input(
            "分析周期",
            value=[]
        )
        
        # 获取数据库中的distinct值
        distinct_values = await db.get_distinct_values()
        
        # 资金类型筛选
        type_options = ["全部"] + distinct_values['types']
        selected_type = st.selectbox(
            "资金类型",
            options=type_options,
            index=0
        )
        
        # 年份筛选
        year_options = ["全部"] + sorted(distinct_values['years'], reverse=True)
        selected_year = st.selectbox(
            "年份",
            options=year_options,
            index=0
        )

    # 主内容区
    try:
        # 从数据库加载数据
        data = await db.load_global_market_data(
            type=None if selected_type == "全部" else selected_type,
            year=None if selected_year == "全部" else int(selected_year)
        )
        
        # 显示气泡图（添加数据验证）
        st.header(f"{selected_year}年全球市场资金分布")
        fig = None
        print(type(data.assets[0]))
        if not data.empty:
            # 检查必要列是否存在
            required_columns = {'currency', 'name', 'assets', 'type'}
            if required_columns.issubset(data.columns):
                try:
                    # 转换decimal assets为float
                    data['assets'] = data['assets'].astype(float)
                    
                    # 生成气泡中心显示的文本
                    data['display_text'] = data.apply(
                        lambda x: f"{x['assets']:.2f}{x['currency']}<br>{x['name']}",
                        axis=1
                    )
                    
                    # 按资产规模排序并计算圆形分布位置
                    data = data.sort_values('assets', ascending=False)
                    
                    # 计算圆形分布坐标(更密集且均匀)
                    n = len(data)
                    radius = data['assets'] / data['assets'].max() * 0.8  # 缩小半径使更密集
                    angle = 2 * np.pi * np.arange(n) / n
                    # 添加随机扰动使分布更自然
                    radius = radius * (0.9 + 0.2 * np.random.rand(n))
                    data['x'] = radius * np.cos(angle)
                    data['y'] = radius * np.sin(angle)
                    
                    # 格式化资产显示
                    data['display_text'] = data.apply(
                        lambda x: f"{int(x['assets']):,d} {x['currency']}<br>{x['name']}",
                        axis=1
                    )
                    
                    fig = px.scatter(
                        data,
                        x="x",
                        y="y",
                        size="assets",
                        color="assets",
                        color_continuous_scale=px.colors.sequential.Viridis,
                        hover_name="name",
                        hover_data={"currency": True, "x": False, "y": False},
                        # title=f"{selected_year}年全球市场资金分布 - {selected_type}",
                        size_max=100,
                        text="display_text"
                    )
                    
                    # 配置气泡文本和布局
                    fig.update_traces(
                        textposition='middle center',
                        textfont=dict(
                            size=10,  # 减小字体大小确保不超出气泡
                            color='white'
                        ),
                        marker=dict(
                            line=dict(
                                width=1,
                                color='DarkSlateGrey'
                            )
                        ),
                        # 自动调整文本大小适应气泡
                        textfont_size=10,
                        textfont_family="Arial"
                    )
                    
                    # 防止气泡重叠和优化布局
                    fig.update_layout(
                        uniformtext_minsize=8,
                        uniformtext_mode='hide',
                        coloraxis_colorbar=dict(
                            title='Assets (Millions)',
                            thickness=20
                        ),
                        # 设置坐标轴范围确保完整显示
                        xaxis=dict(
                            title='2024 Hedge Fund',
                            tickangle=0,
                            showticklabels=False,
                            range=[-1.2, 1.2]  # 扩大x轴范围
                        ),
                        yaxis=dict(
                            title='Assets (Millions)',
                            range=[-1.2, 1.2]  # 扩大y轴范围
                        ),
                        # 调整边距和容器大小
                        margin=dict(l=50, r=50, b=50, t=50, pad=10),
                        width=1200,
                        height=800,
                        # 设置最小气泡间距
                        scattermode='group',
                        scattergap=0.05  # 减小间距使更密集
                    )
                except Exception as e:
                    st.error(f"创建图表失败: {str(e)}")
            else:
                st.warning(f"数据缺少必要列，当前列名: {list(data.columns)}")
        
        if fig is not None:
            # 使用类型和年份生成唯一key
            chart_key = f"global_market_{selected_type}_{selected_year}"
            st.plotly_chart(fig, use_container_width=True, key=chart_key)
        
        # 显示数据表格
        st.header("详细数据")
        st.dataframe(data)
        
    except Exception as e:
        st.error(f"加载数据失败: {str(e)}")

if __name__ == '__main__':
    import asyncio
    asyncio.run(show_global_market())
