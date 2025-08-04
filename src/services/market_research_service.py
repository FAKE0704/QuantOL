from typing import List, Dict
import pandas as pd
import plotly.graph_objects as go
from core.data.data_source import DataSource
from core.data.market_data_source import MarketDataSource
from services.chart_service import ChartService, DataBundle

class MarketResearchService:
    """市场研究核心服务"""
    
    def __init__(self, data_source: str = "tushare"):
        """
        初始化服务
        :param data_source: 数据源类型 (tushare/yahoo)
        """
        self.data_loader = MarketDataSource(api_key="", base_url="")
        self.chart_service = ChartService(
            data_loader=self.data_loader,
            template="plotly_white"
        )
        
    def get_available_fields(self, symbol: str) -> List[str]:
        """获取指定标的可用数据字段"""
        return self.data_loader.get_available_fields(symbol)
    
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
        return self.chart_service.create_combined_chart(config)
    
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
        # TODO: 集成AI服务
        return f"# AI分析报告\n\n## {chart_config.get('title', '未命名图表')}\n\n报告生成中..."
    
    def _load_data(self, symbol: str, fields: List[str]) -> pd.DataFrame:
        """加载市场数据"""
        try:
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
            raise RuntimeError(f"加载{symbol}数据失败: {str(e)}")

if __name__ == "__main__":
    # 测试代码
    service = MarketResearchService()
    print(service.get_available_fields("SH600000"))