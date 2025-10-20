import streamlit as st
import logging
from src.services.market_research_service import MarketResearchService

async def show_market_research_page():
    """显示市场研究主页面"""
    logger = logging.getLogger(__name__)
    logger.info("市场研究页面加载")
    
    st.title("📊 市场研究")
    
    # 研究主题和思路输入
    research_topic = st.text_input("研究主题", placeholder="请输入研究主题")
    st.subheader("研究思路")
    research_idea = st.text_area("", placeholder="请输入研究思路")
    
    # 初始化服务
    research_service = MarketResearchService()
    
    # 参数配置区域
    with st.expander("⚙️ 研究参数配置", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            symbol = st.text_input("股票代码", value="SH600000")
            start_date = st.date_input("开始日期")
            end_date = st.date_input("结束日期")
            
        with col2:
            chart_type = st.selectbox(
                "图表类型",
                options=["K线图", "成交量", "资金流向"]
            )
            analysis_type = st.selectbox(
                "分析类型", 
                options=["技术分析", "基本面分析", "市场情绪分析"]
            )
    
    # 执行研究按钮
    if st.button("开始研究", type="primary"):
        logger.info("研究开始 | 股票代码: %s | 开始日期: %s | 结束日期: %s | 图表类型: %s | 分析类型: %s",
                   symbol, start_date, end_date, chart_type, analysis_type)
        
        with st.spinner("正在生成研究报告..."):
            try:
                # 获取可用字段
                fields = research_service.get_available_fields(symbol)
                
                # 生成图表
                fig = research_service.generate_chart(
                    symbol=symbol,
                    fields=fields[:3],  # 取前3个字段
                    chart_type=chart_type
                )
                
                # 显示结果
                st.plotly_chart(fig, use_container_width=True)
                logger.info("图表生成成功 | 股票代码: %s | 图表类型: %s", symbol, chart_type)
                
                # 生成分析报告
                report = research_service.generate_analysis_report(
                    chart_config={"title": f"{symbol}分析报告"},
                    data_summary={"symbol": symbol}
                )
                st.markdown(report)
                logger.info("研究报告生成完成 | 股票代码: %s", symbol)
                
            except Exception as e:
                logger.error("研究失败 | 股票代码: %s | 错误: %s", symbol, str(e))
                st.error(f"研究失败: {str(e)}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(show_market_research_page())