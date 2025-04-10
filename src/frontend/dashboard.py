import streamlit as st
import plotly.express as px
from services.chart_service import ChartService
from services.theme_manager import ThemeManager
from services.interaction_service import InteractionService
# from services.policy_service import PolicyService
import pandas as pd
from datetime import datetime

def show_dashboard():
    # 初始化服务
    theme_manager = ThemeManager()
    interaction_service = InteractionService()
    # policy_service = PolicyService() # 初始化政策获取服务
    
    # 页面标题
    st.title('量化投资仪表盘')
    
    # 三栏布局
    col1, col2, col3 = st.columns([1, 1, 1])
    
    # 资金流图表
    with col1:
        st.header('资金流向分析')
        from core.data.akshare_source import AkShareSource
        akshare = AkShareSource()
        akshare['date'] = pd.to_datetime(akshare['date'])
        try:
            fund_flow = akshare.get_market_fund_flow()
            # debug
            st.write(fund_flow)

            # 使用实际的列名绘制资金流向图
            fig = px.line(
                fund_flow,
                x='date',
                y=['主力净流入-净额', '超大单净流入-净额', '大单净流入-净额', '中单净流入-净额', '小单净流入-净额'],
                labels={
                    'value': '资金流向 (亿)',
                    'date': '日期',
                    'variable': '资金类型'
                },
                title='大盘资金流向分析'
            )
            fig.update_layout(
                legend_title_text='资金类型',
                xaxis_title='日期',
                yaxis_title='资金流向 (亿)'
            )
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.error(f"获取资金流向数据失败: {str(e)}")
        
    # K线图表 
    with col2:
        st.header('K线走势')
        # 这里将添加K线图表调用逻辑
        
    # 技术指标
    with col3:
        st.header('技术指标')
        # 这里将添加技术指标图表调用逻辑
        
    # 侧边栏控制面板
    with st.sidebar:
        st.header('控制面板')
        # 主题选择
        theme = st.selectbox(
            "主题模式",
            options=list(theme_manager.themes.keys()),
            index=0
        )
        
        # 时间范围选择
        date_range = st.date_input(
            "分析周期",
            value=[]
        )
        
        # 政策监控面板
        with st.expander("中美政策监控", expanded=True):
            threshold = st.slider(
                "预警敏感度",
                min_value=0.0, 
                max_value=1.0,
                value=0.7,
                step=0.1,
                help="调整政策影响预警的敏感程度"
            )
            
            if st.button("刷新政策事件"):
                pass
                # st.session_state.policy_events = policy_service.get_recent_events()
                
            if 'policy_events' in st.session_state:
                for event in st.session_state.policy_events:
                    bg_color = "#ffcccc" if event.impact_score > threshold else "#ffffcc"
                    opacity = min(0.3 + (event.impact_score * 0.7), 1.0)
                    st.markdown(f"""
                    <div style="padding:10px;margin:5px;border-radius:5px;
                                background:{bg_color};opacity:{opacity};
                                border-left:4px solid {bg_color}">
                        <b>{event.event_date.strftime('%Y-%m-%d %H:%M')}</b> | {event.policy_type}
                        <br>影响分数: {event.impact_score:.2f}
                    </div>
                    """, unsafe_allow_html=True)

if __name__ == '__main__':
    show_dashboard()
