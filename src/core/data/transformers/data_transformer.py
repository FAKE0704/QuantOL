"""
数据格式标准化器 - 负责统一各数据源格式
职责：将不同数据源的数据转换为系统统一的标准格式
"""

import pandas as pd
from typing import Dict, Any, List
import logging
from datetime import datetime, date


class DataTransformerError(Exception):
    """数据转换错误"""
    pass


class DataTransformer:
    """数据格式标准化器 - 负责统一各数据源格式"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

        # 统一的字段映射
        self.stock_basic_field_mapping = {
            'tushare': {
                'ts_code': 'symbol_code',
                'symbol': 'symbol',
                'name': 'name',
                'area': 'region',
                'industry': 'industry',
                'market': 'market',
                'list_date': 'list_date',
                'act_name': 'actual_controller',
                'act_ent_type': 'controller_type'
            },
            'baostock': {
                'code': 'symbol',
                'code_name': 'name',
                'ipoDate': 'list_date',
                'type': 'stock_type',
                'status': 'status'
            }
        }

        self.market_data_field_mapping = {
            'tushare': {
                'ts_code': 'symbol_code',
                'trade_date': 'date',
                'open': 'open',
                'high': 'high',
                'low': 'low',
                'close': 'close',
                'pre_close': 'prev_close',
                'change': 'change',
                'pct_chg': 'pct_change',
                'vol': 'volume',
                'amount': 'amount'
            },
            'baostock': {
                'code': 'symbol',
                'date': 'date',
                'open': 'open',
                'high': 'high',
                'low': 'low',
                'close': 'close',
                'preclose': 'prev_close',
                'volume': 'volume',
                'amount': 'amount'
            }
        }

    @staticmethod
    def standardize_date_format(date_value: Any, source_format: str = 'auto') -> str:
        """
        标准化日期格式

        Args:
            date_value: 日期值
            source_format: 源格式 ('YYYYMMDD', 'YYYY-MM-DD', 'auto')

        Returns:
            格式为YYYY-MM-DD的日期字符串
        """
        if pd.isna(date_value) or date_value == '':
            return ''

        try:
            if isinstance(date_value, str):
                if source_format == 'auto':
                    # 自动检测格式
                    if len(date_value) == 8 and date_value.isdigit():
                        # YYYYMMDD格式
                        return f"{date_value[:4]}-{date_value[4:6]}-{date_value[6:8]}"
                    elif '-' in date_value:
                        # 已经是标准格式
                        return date_value
                elif source_format == 'YYYYMMDD':
                    return f"{date_value[:4]}-{date_value[4:6]}-{date_value[6:8]}"

            elif isinstance(date_value, (datetime, date)):
                return date_value.strftime('%Y-%m-%d')

            return str(date_value)

        except Exception:
            return str(date_value)

    def transform_stock_basic(self, df: pd.DataFrame, source: str = "tushare") -> pd.DataFrame:
        """
        转换股票基本信息格式

        Args:
            df: 原始数据
            source: 数据源类型 ('tushare', 'baostock')

        Returns:
            标准化后的DataFrame
        """
        try:
            if df.empty:
                return df

            # 获取字段映射
            if source not in self.stock_basic_field_mapping:
                raise DataTransformerError(f"不支持的数据源: {source}")

            field_mapping = self.stock_basic_field_mapping[source]

            # 重命名字段
            transformed_df = df.rename(columns=field_mapping)

            # 确保必要字段存在
            required_fields = ['symbol_code', 'symbol', 'name', 'list_date']
            for field in required_fields:
                if field not in transformed_df.columns:
                    transformed_df[field] = None

            # 标准化日期格式
            if 'list_date' in transformed_df.columns:
                transformed_df['list_date'] = transformed_df['list_date'].apply(
                    lambda x: self.standardize_date_format(x, 'YYYYMMDD' if source == 'tushare' else 'auto')
                )

            # 添加转换时间戳
            transformed_df['transformed_at'] = datetime.now()
            transformed_df['data_source'] = source

            # 字段类型转换
            if 'symbol' in transformed_df.columns:
                transformed_df['symbol'] = transformed_df['symbol'].astype(str)

            self.logger.info(f"成功转换 {len(transformed_df)} 条股票基本信息，来源: {source}")
            return transformed_df

        except Exception as e:
            self.logger.error(f"股票基本信息转换失败: {e}")
            raise DataTransformerError(f"股票基本信息转换失败: {e}")

    def transform_market_data(self, df: pd.DataFrame, source: str = "tushare") -> pd.DataFrame:
        """
        转换市场数据格式

        Args:
            df: 原始数据
            source: 数据源类型 ('tushare', 'baostock')

        Returns:
            标准化后的DataFrame
        """
        try:
            if df.empty:
                return df

            # 获取字段映射
            if source not in self.market_data_field_mapping:
                raise DataTransformerError(f"不支持的数据源: {source}")

            field_mapping = self.market_data_field_mapping[source]

            # 重命名字段
            transformed_df = df.rename(columns=field_mapping)

            # 确保必要字段存在
            required_fields = ['symbol_code', 'date', 'open', 'high', 'low', 'close']
            for field in required_fields:
                if field not in transformed_df.columns:
                    if field == 'symbol_code' and 'symbol' in transformed_df.columns:
                        transformed_df['symbol_code'] = transformed_df['symbol']
                    else:
                        transformed_df[field] = None

            # 标准化日期格式
            if 'date' in transformed_df.columns:
                date_format = 'YYYYMMDD' if source == 'tushare' else 'auto'
                transformed_df['date'] = transformed_df['date'].apply(
                    lambda x: self.standardize_date_format(x, date_format)
                )

            # 数值字段类型转换
            numeric_fields = ['open', 'high', 'low', 'close', 'volume', 'amount', 'prev_close', 'change', 'pct_change']
            for field in numeric_fields:
                if field in transformed_df.columns:
                    transformed_df[field] = pd.to_numeric(transformed_df[field], errors='coerce')

            # 计算缺失字段
            if 'prev_close' in transformed_df.columns and 'close' in transformed_df.columns and 'change' in transformed_df.columns:
                # 如果change字段为空，尝试计算
                mask = (transformed_df['change'].isna()) & (transformed_df['prev_close'].notna()) & (transformed_df['close'].notna())
                transformed_df.loc[mask, 'change'] = transformed_df.loc[mask, 'close'] - transformed_df.loc[mask, 'prev_close']

            if 'prev_close' in transformed_df.columns and 'close' in transformed_df.columns and 'pct_change' in transformed_df.columns:
                # 如果pct_change字段为空，尝试计算
                mask = (transformed_df['pct_change'].isna()) & (transformed_df['prev_close'].notna()) & (transformed_df['close'].notna()) & (transformed_df.loc[:, 'prev_close'] != 0)
                transformed_df.loc[mask, 'pct_change'] = (
                    (transformed_df.loc[mask, 'close'] - transformed_df.loc[mask, 'prev_close'])
                    / transformed_df.loc[mask, 'prev_close'] * 100
                )

            # 添加转换时间戳
            transformed_df['transformed_at'] = datetime.now()
            transformed_df['data_source'] = source

            # 按日期排序
            if 'date' in transformed_df.columns:
                transformed_df = transformed_df.sort_values('date').reset_index(drop=True)

            self.logger.info(f"成功转换 {len(transformed_df)} 条市场数据，来源: {source}")
            return transformed_df

        except Exception as e:
            self.logger.error(f"市场数据转换失败: {e}")
            raise DataTransformerError(f"市场数据转换失败: {e}")

    def transform_financial_data(self, df: pd.DataFrame, source: str = "tushare") -> pd.DataFrame:
        """
        转换财务数据格式

        Args:
            df: 原始数据
            source: 数据源类型

        Returns:
            标准化后的DataFrame
        """
        try:
            if df.empty:
                return df

            # 保留原始字段，添加标准化字段
            transformed_df = df.copy()

            # 标准化日期格式
            if 'end_date' in transformed_df.columns:
                transformed_df['report_date'] = transformed_df['end_date'].apply(
                    lambda x: self.standardize_date_format(x, 'YYYYMMDD')
                )

            # 数值字段类型转换
            numeric_fields = [
                'total_revenue', 'revenue', 'total_cogs', 'oper_cost', 'admin_exp',
                'fin_exp', 'impair_tobond', 'impair_tostock', 'credit_impair',
                'total_profit', 'n_income', 'n_income_attr_p', 'basic_eps',
                'diluted_eps', 'total_assets', 'total_equity'
            ]

            for field in numeric_fields:
                if field in transformed_df.columns:
                    transformed_df[field] = pd.to_numeric(transformed_df[field], errors='coerce')

            # 添加转换时间戳
            transformed_df['transformed_at'] = datetime.now()
            transformed_df['data_source'] = source

            self.logger.info(f"成功转换 {len(transformed_df)} 条财务数据，来源: {source}")
            return transformed_df

        except Exception as e:
            self.logger.error(f"财务数据转换失败: {e}")
            raise DataTransformerError(f"财务数据转换失败: {e}")

    def transform_index_data(self, df: pd.DataFrame, source: str = "tushare") -> pd.DataFrame:
        """
        转换指数数据格式

        Args:
            df: 原始数据
            source: 数据源类型

        Returns:
            标准化后的DataFrame
        """
        try:
            if df.empty:
                return df

            # 指数基本信息转换
            if 'ts_code' in df.columns or 'index_code' in df.columns:
                transformed_df = df.rename(columns={
                    'ts_code': 'symbol_code',
                    'index_code': 'symbol_code',
                    'name': 'name',
                    'fullname': 'full_name',
                    'market': 'market',
                    'publisher': 'publisher',
                    'base_date': 'base_date',
                    'base_point': 'base_point'
                })

                # 标准化日期格式
                if 'base_date' in transformed_df.columns:
                    transformed_df['base_date'] = transformed_df['base_date'].apply(
                        lambda x: self.standardize_date_format(x, 'YYYYMMDD')
                    )

            # 指数行情数据转换
            elif 'trade_date' in df.columns:
                transformed_df = df.rename(columns={
                    'ts_code': 'symbol_code',
                    'trade_date': 'date',
                    'open': 'open',
                    'high': 'high',
                    'low': 'low',
                    'close': 'close',
                    'pre_close': 'prev_close',
                    'change': 'change',
                    'pct_chg': 'pct_change',
                    'vol': 'volume',
                    'amount': 'amount'
                })

                # 标准化日期格式
                if 'date' in transformed_df.columns:
                    transformed_df['date'] = transformed_df['date'].apply(
                        lambda x: self.standardize_date_format(x, 'YYYYMMDD')
                    )

                # 数值字段类型转换
                numeric_fields = ['open', 'high', 'low', 'close', 'volume', 'amount', 'prev_close', 'change', 'pct_change']
                for field in numeric_fields:
                    if field in transformed_df.columns:
                        transformed_df[field] = pd.to_numeric(transformed_df[field], errors='coerce')

            else:
                transformed_df = df.copy()

            # 添加转换时间戳
            transformed_df['transformed_at'] = datetime.now()
            transformed_df['data_source'] = source

            self.logger.info(f"成功转换 {len(transformed_df)} 条指数数据，来源: {source}")
            return transformed_df

        except Exception as e:
            self.logger.error(f"指数数据转换失败: {e}")
            raise DataTransformerError(f"指数数据转换失败: {e}")

    def validate_transformed_data(self, df: pd.DataFrame, data_type: str) -> Dict[str, Any]:
        """
        验证转换后的数据质量

        Args:
            df: 转换后的数据
            data_type: 数据类型 ('stock_basic', 'market_data', 'financial_data', 'index_data')

        Returns:
            验证结果字典
        """
        try:
            validation_result = {
                'valid': True,
                'errors': [],
                'warnings': [],
                'stats': {
                    'total_records': len(df),
                    'null_records': 0,
                    'duplicate_records': 0
                }
            }

            if df.empty:
                validation_result['valid'] = False
                validation_result['errors'].append("数据为空")
                return validation_result

            # 基本验证
            validation_result['stats']['null_records'] = df.isnull().sum().sum()
            validation_result['stats']['duplicate_records'] = df.duplicated().sum()

            # 根据数据类型进行特定验证
            if data_type == 'stock_basic':
                required_fields = ['symbol_code', 'symbol', 'name']
                for field in required_fields:
                    if field not in df.columns:
                        validation_result['valid'] = False
                        validation_result['errors'].append(f"缺少必要字段: {field}")
                    elif df[field].isnull().any():
                        validation_result['warnings'].append(f"字段 {field} 存在空值")

            elif data_type == 'market_data':
                required_fields = ['symbol_code', 'date', 'open', 'high', 'low', 'close']
                for field in required_fields:
                    if field not in df.columns:
                        validation_result['valid'] = False
                        validation_result['errors'].append(f"缺少必要字段: {field}")

                # 检查价格逻辑性
                if all(field in df.columns for field in ['open', 'high', 'low', 'close']):
                    invalid_prices = (df['high'] < df['low']) | (df['high'] < df['open']) | (df['high'] < df['close']) | (df['low'] > df['open']) | (df['low'] > df['close'])
                    if invalid_prices.any():
                        validation_result['warnings'].append(f"发现 {invalid_prices.sum()} 条价格逻辑异常的数据")

            # 记录验证结果
            if validation_result['valid']:
                self.logger.info(f"数据验证通过，{data_type}: {len(df)} 条记录")
            else:
                self.logger.warning(f"数据验证失败，{data_type}: {validation_result['errors']}")

            return validation_result

        except Exception as e:
            self.logger.error(f"数据验证失败: {e}")
            return {
                'valid': False,
                'errors': [f"验证过程出错: {e}"],
                'warnings': [],
                'stats': {}
            }