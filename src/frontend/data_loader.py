import streamlit as st
import pandas as pd
from typing import Dict, Any, List, Tuple
from core.strategy.backtesting import BacktestConfig

class DataLoader:
    """数据加载服务，负责统一的数据加载和预处理"""

    def __init__(self, session_state):
        self.session_state = session_state

    async def load_backtest_data(self, backtest_config: BacktestConfig) -> Dict[str, Any]:
        """加载回测数据"""
        symbols = backtest_config.get_symbols()

        if backtest_config.is_multi_symbol():
            return await self._load_multiple_stock_data(backtest_config, symbols)
        else:
            return await self._load_single_stock_data(backtest_config, symbols[0])

    async def _load_single_stock_data(self, config: BacktestConfig, symbol: str) -> Dict[str, Any]:
        """加载单股票数据"""
        try:
            data = await self.session_state.db.load_stock_data(
                symbol, config.start_date, config.end_date, config.frequency
            )

            st.info(f"已加载 {symbol} 数据: {len(data)} 条记录")
            return {"data": data, "symbol": symbol}

        except Exception as e:
            st.error(f"加载股票数据失败: {e}")
            return {"data": pd.DataFrame(), "symbol": symbol, "error": str(e)}

    async def _load_multiple_stock_data(self, config: BacktestConfig, symbols: List[str]) -> Dict[str, Any]:
        """加载多股票数据"""
        try:
            data = await self.session_state.db.load_multiple_stock_data(
                symbols, config.start_date, config.end_date, config.frequency
            )

            st.info(f"已加载 {len(data)} 只股票数据")
            return {"data": data, "symbols": symbols}

        except Exception as e:
            st.error(f"加载多股票数据失败: {e}")
            return {"data": {}, "symbols": symbols, "error": str(e)}

    def prepare_engine_data(self, loaded_data: Dict[str, Any], config: BacktestConfig) -> Any:
        """准备引擎数据"""
        if config.is_multi_symbol():
            return loaded_data["data"]
        else:
            return loaded_data["data"]

    def validate_data_quality(self, data: Any, config: BacktestConfig) -> bool:
        """验证数据质量"""
        if config.is_multi_symbol():
            if not isinstance(data, dict) or not data:
                st.warning("多股票数据为空或格式不正确")
                return False

            for symbol, symbol_data in data.items():
                if symbol_data.empty:
                    st.warning(f"股票 {symbol} 数据为空")
                    return False
                if len(symbol_data) < 2:
                    st.warning(f"股票 {symbol} 数据不足，至少需要2条记录")
                    return False
            return True

        else:
            if data.empty:
                st.warning("股票数据为空")
                return False
            if len(data) < 2:
                st.warning("数据不足，至少需要2条记录")
                return False
            return True

    def get_data_summary(self, data: Any, config: BacktestConfig) -> str:
        """获取数据摘要"""
        if config.is_multi_symbol():
            symbol_count = len(data)
            total_records = sum(len(df) for df in data.values())
            return f"{symbol_count}只股票，共{total_records}条记录"
        else:
            return f"{len(data)}条记录"

    async def refresh_stock_list(self) -> List[Tuple[str, str]]:
        """刷新股票列表"""
        try:
            stock_list = await self.session_state.db.get_all_stocks()
            return [
                (row['code'], f"{row['code']} - {row['code_name']}")
                for _, row in stock_list.iterrows()
            ]
        except Exception as e:
            st.error(f"刷新股票列表失败: {e}")
            return []