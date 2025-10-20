from typing import List, Dict
import pandas as pd
import plotly.graph_objects as go
import logging
from src.core.data.data_source import DataSource
from src.core.data.market_data_source import MarketDataSource
from src.services.chart_service import ChartService, DataBundle

class MarketResearchService:
    """市场研究核心服务"""
    
    def __init__(self, data_source: str = "tushare"):
        """
        初始化服务
        :param data_source: 数据源类型 (tushare/yahoo)
        """
        self.logger = logging.getLogger(__name__)
        self.logger.info("市场研究服务初始化 | 数据源: %s", data_source)
        
        self.data_loader = MarketDataSource(api_key="", base_url="")
        # 初始化DataBundle
        data_bundle = DataBundle()
        self.chart_service = ChartService(data_bundle=data_bundle)
        
    def get_available_fields(self, symbol: str) -> List[str]:
        """获取指定标的可用数据字段"""
        self.logger.info("获取可用字段 | 标的: %s", symbol)
        fields = self.data_loader.get_available_fields(symbol)
        self.logger.info("获取可用字段完成 | 标的: %s | 字段数: %d", symbol, len(fields))
        return fields
    
    def generate_chart(
        self,
        symbol: str,
        fields: List[str],
        chart_type: str = "K线图",
        **kwargs
    ) -> go.Figure:
        """
        生成金融数据图表
        :param symbol: 标的代码
        :param fields: 需要展示的字段
        :param chart_type: 图表类型 (K线图/成交量/资金流向)
        :return: Plotly图表对象
        """
        self.logger.info("生成图表开始 | 标的: %s | 图表类型: %s | 字段: %s",
                       symbol, chart_type, fields)
        # 加载数据
        data = self._load_data(symbol, fields)
        
        # 准备DataBundle
        data_bundle = DataBundle(raw_data=data)
        
        # 生成图表配置
        config = {
            "main_chart": {
                "type": chart_type,
                "fields": fields,
                "data_source": "kline_data",
                "style": kwargs.get("style", {})
            },
            "sub_chart": {
                "show": False
            }
        }
        
        # 生成图表
        fig = self.chart_service.create_combined_chart(config)
        self.logger.info("图表生成完成 | 标的: %s | 图表类型: %s", symbol, chart_type)
        return fig
    
    def generate_analysis_report(
        self, 
        chart_config: Dict,
        data_summary: Dict
    ) -> str:
        """
        生成AI分析报告
        :param chart_config: 图表配置信息
        :param data_summary: 数据摘要
        :return: Markdown格式分析报告
        """
        self.logger.info("生成分析报告 | 图表标题: %s", chart_config.get('title', '未命名图表'))
        # TODO: 集成AI服务
        report = f"# AI分析报告\n\n## {chart_config.get('title', '未命名图表')}\n\n报告生成中..."
        self.logger.info("分析报告生成完成 | 图表标题: %s", chart_config.get('title', '未命名图表'))
        return report
    
    def _load_data(self, symbol: str, fields: List[str]) -> pd.DataFrame:
        """加载市场数据"""
        try:
            self.logger.debug("加载市场数据 | 标的: %s | 字段: %s", symbol, fields)
            # 从数据加载器获取数据
            data = self.data_loader.get_data(symbol=symbol, fields=fields)
            
            # 确保返回DataFrame且包含所需字段
            if not isinstance(data, pd.DataFrame):
                raise ValueError("数据加载器返回的不是DataFrame")
                
            missing_fields = [f for f in fields if f not in data.columns]
            if missing_fields:
                raise ValueError(f"缺少必要字段: {missing_fields}")
                
            return data
            
        except Exception as e:
            self.logger.error("加载市场数据失败 | 标的: %s | 错误: %s", symbol, str(e))
            raise RuntimeError(f"加载{symbol}数据失败: {str(e)}")

if __name__ == "__main__":
    # 测试代码
    service = MarketResearchService()
    print(service.get_available_fields("SH600000"))