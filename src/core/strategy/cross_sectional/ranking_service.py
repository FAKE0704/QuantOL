"""横截面排名服务模块"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any
from datetime import datetime

from src.core.strategy.indicators import IndicatorService
from src.core.strategy.rule_parser import RuleParser
from src.support.log.logger import logger
from src.core.strategy.cross_sectional.ranking_config import RankingConfig


class CrossSectionalRankingService:
    """横截面排名服务

    提供横截面因子计算、排名和标的筛选功能。
    """

    def __init__(self, indicator_service: IndicatorService, ranking_config: RankingConfig):
        """

        Args:
            indicator_service: 指标计算服务
            ranking_config: 排名配置
        """
        self.indicator_service = indicator_service
        self.config = ranking_config
        self._rule_parsers: Dict[str, RuleParser] = {}
        self._last_ranking: Optional[pd.DataFrame] = None

    def _get_or_create_rule_parser(
        self,
        symbol: str,
        data: pd.DataFrame,
        portfolio_manager: Any = None
    ) -> RuleParser:
        """获取或创建规则解析器

        Args:
            symbol: 标的代码
            data: 市场数据
            portfolio_manager: 投资组合管理器

        Returns:
            RuleParser实例
        """
        if symbol not in self._rule_parsers:
            parser = RuleParser(data, self.indicator_service, portfolio_manager)
            self._rule_parsers[symbol] = parser
        else:
            # 更新数据引用
            self._rule_parsers[symbol].data = data
            if portfolio_manager:
                self._rule_parsers[symbol].portfolio_manager = portfolio_manager

        return self._rule_parsers[symbol]

    def calculate_cross_sectional_factor(
        self,
        data_dict: Dict[str, pd.DataFrame],
        timestamp: pd.Timestamp,
        portfolio_manager: Any = None
    ) -> pd.Series:
        """计算横截面因子值

        Args:
            data_dict: 所有标的的市场数据字典 {symbol: DataFrame}
            timestamp: 当前时间点
            portfolio_manager: 投资组合管理器

        Returns:
            因子值Series，索引为symbol，值为因子值
        """
        factor_values = {}

        for symbol, data in data_dict.items():
            try:
                # 获取该时间点的索引
                if timestamp not in data.index:
                    # 尝试通过combined_time列查找
                    if 'combined_time' in data.columns:
                        mask = data['combined_time'] == timestamp
                        if mask.any():
                            idx = mask.idxmax()
                        else:
                            logger.debug(f"标的 {symbol} 在时间 {timestamp} 无数据")
                            factor_values[symbol] = np.nan
                            continue
                    else:
                        logger.debug(f"标的 {symbol} 在时间 {timestamp} 无数据")
                        factor_values[symbol] = np.nan
                        continue
                else:
                    idx = timestamp

                # 获取或创建规则解析器
                parser = self._get_or_create_rule_parser(symbol, data, portfolio_manager)

                # 设置当前索引
                if isinstance(idx, pd.Timestamp):
                    try:
                        idx = data.index.get_loc(idx)
                    except KeyError:
                        factor_values[symbol] = np.nan
                        continue

                parser.current_index = idx

                # 计算因子值
                factor_value = parser.parse(self.config.factor_expression, mode='factor')
                factor_values[symbol] = factor_value

            except Exception as e:
                logger.warning(f"计算标的 {symbol} 的因子值失败: {str(e)}")
                factor_values[symbol] = np.nan

        # 转换为Series
        factor_series = pd.Series(factor_values, dtype=float)
        logger.info(f"横截面因子计算完成，有效值数量: {factor_series.notna().sum()}/{len(factor_series)}")

        return factor_series

    def apply_filters(
        self,
        data_dict: Dict[str, pd.DataFrame],
        timestamp: pd.Timestamp,
        factor_values: pd.Series
    ) -> pd.Series:
        """应用过滤条件

        Args:
            data_dict: 所有标的的市场数据字典
            timestamp: 当前时间点
            factor_values: 因子值Series

        Returns:
            过滤后的因子值Series
        """
        filtered_values = factor_values.copy()

        for symbol in factor_values.index:
            if pd.isna(factor_values[symbol]):
                filtered_values[symbol] = np.nan
                continue

            data = data_dict.get(symbol)
            if data is None:
                filtered_values[symbol] = np.nan
                continue

            # 获取该时间点的数据
            if timestamp in data.index:
                row = data.loc[timestamp]
            elif 'combined_time' in data.columns:
                mask = data['combined_time'] == timestamp
                if mask.any():
                    row = data.loc[mask.idxmax()]
                else:
                    filtered_values[symbol] = np.nan
                    continue
            else:
                filtered_values[symbol] = np.nan
                continue

            # 应用价格过滤
            if self.config.min_price is not None:
                price = row.get('close', row.get('price', 0))
                if pd.isna(price) or price < self.config.min_price:
                    filtered_values[symbol] = np.nan
                    continue

            # 应用成交量过滤
            if self.config.min_volume is not None:
                volume = row.get('volume', 0)
                if pd.isna(volume) or volume < self.config.min_volume:
                    filtered_values[symbol] = np.nan
                    continue

        logger.info(f"过滤后有效值数量: {filtered_values.notna().sum()}/{len(filtered_values)}")
        return filtered_values

    def rank_symbols(
        self,
        factor_values: pd.Series,
        ascending: Optional[bool] = None
    ) -> pd.DataFrame:
        """对标的进行排名

        Args:
            factor_values: 因子值Series
            ascending: 是否升序排列，None则根据配置自动判断

        Returns:
            排名结果DataFrame，包含列：symbol, factor_value, rank
        """
        if ascending is None:
            ascending = (self.config.ranking_method == "ascending")

        # 创建结果DataFrame
        result_df = pd.DataFrame({
            'symbol': factor_values.index,
            'factor_value': factor_values.values
        })

        # 过滤NaN值
        result_df = result_df.dropna(subset=['factor_value'])

        # 排名
        result_df['rank'] = result_df['factor_value'].rank(ascending=ascending, method='min')

        # 按排名排序
        result_df = result_df.sort_values('rank')

        # 重置索引
        result_df = result_df.reset_index(drop=True)

        self._last_ranking = result_df
        logger.info(f"排名完成，共 {len(result_df)} 个标的进入排名")
        logger.info(f"前5名: {result_df.head(5)[['symbol', 'factor_value', 'rank']].to_dict('records')}")

        return result_df

    def get_selected_symbols(
        self,
        ranking_df: pd.DataFrame
    ) -> List[str]:
        """根据top_n获取选中标的列表

        Args:
            ranking_df: 排名结果DataFrame

        Returns:
            选中标的代码列表
        """
        top_df = ranking_df.head(self.config.top_n)
        selected = top_df['symbol'].tolist()
        logger.info(f"选中标的列表（前{self.config.top_n}名）: {selected}")
        return selected

    def get_position_weights(
        self,
        selected_symbols: List[str]
    ) -> Dict[str, float]:
        """获取选中标的的仓位权重

        Args:
            selected_symbols: 选中标的列表

        Returns:
            标的权重字典 {symbol: weight}
        """
        # 平均分配权重
        num_symbols = len(selected_symbols)
        if num_symbols == 0:
            return {}

        weight = min(1.0 / num_symbols, self.config.max_position_percent)
        weights = {symbol: weight for symbol in selected_symbols}

        logger.info(f"仓位权重分配: {weights}")
        return weights

    def should_rebalance(self, timestamp: pd.Timestamp, last_rebalance_date: Optional[pd.Timestamp] = None) -> bool:
        """判断是否需要再平衡

        Args:
            timestamp: 当前时间
            last_rebalance_date: 上次再平衡日期

        Returns:
            是否需要再平衡
        """
        if self.config.rebalance_frequency == "daily":
            # 每日再平衡，总是返回True（除非同一天已经再平衡过）
            if last_rebalance_date is None:
                return True
            return timestamp.date() != last_rebalance_date.date()

        elif self.config.rebalance_frequency == "weekly":
            # 检查是否是目标星期几
            if timestamp.weekday() + 1 == self.config.rebalance_day:
                # 确保距离上次再平衡至少一周（或从未再平衡）
                if last_rebalance_date is None or (timestamp - last_rebalance_date).days >= 7:
                    return True

        elif self.config.rebalance_frequency == "monthly":
            # 检查是否是目标日期
            if timestamp.day == self.config.rebalance_day:
                # 确保距离上次再平衡至少一个月（或从未再平衡）
                if last_rebalance_date is None or (timestamp - last_rebalance_date).days >= 28:
                    return True

        return False

    def get_last_ranking(self) -> Optional[pd.DataFrame]:
        """获取最后一次排名结果"""
        return self._last_ranking
