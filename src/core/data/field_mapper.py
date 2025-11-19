"""
数据源字段映射器
解决不同数据源字段名称差异的问题
"""

from typing import Dict, List, Optional, Any
import pandas as pd
from datetime import datetime
from src.support.log.logger import logger


class FieldMapper:
    """数据源字段映射器"""

    # 数据源字段映射配置
    SOURCE_FIELD_MAPPINGS = {
        'baostock': {
            'code': 'code',
            'code_name': 'code_name',  # Baostock直接返回code_name字段
            'ipo_date': 'ipoDate',
            'out_date': 'outDate',
            'type': 'type',
            'status': 'status'  # 添加status字段映射
        },
        'tushare': {
            'code': 'ts_code',          # 带交易所后缀的完整代码
            'code_name': 'name',        # 股票名称映射到code_name
            'ipo_date': 'list_date',
            'status': 'list_status',
            'market': 'market'
        }
    }

    # 状态值映射
    STATUS_MAPPING = {
        'tushare': {
            'L': '上市',
            'D': '退市',
            'P': '暂停'
        },
        'baostock': {
            '1': '上市',    # Baostock type=1 表示股票
            '0': '其他'
        }
    }

    # 类型值映射
    TYPE_MAPPING = {
        'baostock': {
            '1': '股票',    # Baostock type=1 表示股票
            '2': '指数',    # Baostock type=2 表示指数
            '0': '其他'
        }
    }

    @classmethod
    def map_to_standard_fields(cls, df: pd.DataFrame, source_type: str) -> pd.DataFrame:
        """
        将数据源的字段映射为数据库标准字段

        Args:
            df: 原始数据DataFrame
            source_type: 数据源类型 ('baostock', 'tushare')

        Returns:
            映射后的DataFrame
        """
        if source_type not in cls.SOURCE_FIELD_MAPPINGS:
            raise ValueError(f"不支持的数据源类型: {source_type}")

        mapping = cls.SOURCE_FIELD_MAPPINGS[source_type]
        result_df = df.copy()

        # 执行字段映射
        rename_dict = {}
        for standard_field, source_field in mapping.items():
            if source_field in df.columns:
                rename_dict[source_field] = standard_field

        if rename_dict:
            result_df = result_df.rename(columns=rename_dict)
            # logger.debug(f"字段映射 {source_type}: {rename_dict}")  # 注释掉减少日志噪音

        # 执行数据转换
        result_df = cls._convert_data_types(result_df, source_type)

        # 添加数据源标识
        result_df['data_source'] = source_type

        # 设置默认值
        result_df = cls._set_default_values(result_df, source_type)

        return result_df

    @classmethod
    def _convert_data_types(cls, df: pd.DataFrame, source_type: str) -> pd.DataFrame:
        """
        转换数据类型和格式

        Args:
            df: 数据DataFrame
            source_type: 数据源类型

        Returns:
            类型转换后的DataFrame
        """
        result_df = df.copy()

        # 日期字段转换
        for date_field in ['ipo_date', 'out_date']:
            if date_field in result_df.columns:
                result_df[date_field] = cls._convert_date_field(result_df[date_field], source_type)

        # 状态和类型字段转换
        if source_type == 'tushare' and 'status' in result_df.columns:
            result_df['status'] = result_df['status'].map(cls.STATUS_MAPPING.get('tushare', {})).fillna('上市')

        if source_type == 'baostock':
            # Baostock的状态和类型转换
            if 'status' in result_df.columns:
                result_df['status'] = result_df['status'].map(cls.STATUS_MAPPING.get('baostock', {})).fillna('上市')
            if 'type' in result_df.columns:
                result_df['type'] = result_df['type'].map(cls.TYPE_MAPPING.get('baostock', {})).fillna('股票')

        return result_df

    @classmethod
    def _convert_date_field(cls, series: pd.Series, source_type: str) -> pd.Series:
        """
        转换日期字段格式

        Args:
            series: 日期字段Series
            source_type: 数据源类型

        Returns:
            转换后的Series
        """
        if source_type == 'tushare':
            # Tushare日期格式：YYYYMMDD -> YYYY-MM-DD
            try:
                # 转换为字符串，确保8位数字格式
                series_str = series.astype(str).str.zfill(8)
                # 转换为datetime格式
                dates = pd.to_datetime(series_str, format='%Y%m%d', errors='coerce')
                # 格式化为YYYY-MM-DD字符串
                return dates.dt.strftime('%Y-%m-%d').where(dates.notna(), None)
            except Exception as e:
                logger.warning(f"Tushare日期字段转换失败: {e}")
                return series
        else:
            # Baostock日期格式：YYYY-MM-DD（已经符合标准）
            try:
                dates = pd.to_datetime(series, errors='coerce')
                return dates.dt.strftime('%Y-%m-%d').where(dates.notna(), None)
            except Exception as e:
                logger.warning(f"日期字段转换失败: {e}")
                return series

    @classmethod
    def _set_default_values(cls, df: pd.DataFrame, source_type: str) -> pd.DataFrame:
        """
        设置默认值

        Args:
            df: 数据DataFrame
            source_type: 数据源类型

        Returns:
            设置默认值后的DataFrame
        """
        result_df = df.copy()

        # 设置股票类型默认值
        if 'type' not in result_df.columns:
            result_df['type'] = '股票'

        # 设置状态默认值
        if 'status' not in result_df.columns:
            if source_type == 'baostock':
                # Baostock返回的都是上市股票
                result_df['status'] = '上市'
            elif source_type == 'tushare':
                # Tushare默认状态为上市，因为通过list_status='L'过滤获取的都是上市股票
                result_df['status'] = '上市'

        # 设置out_date默认值（大部分股票都没有退市日期）
        if 'out_date' not in result_df.columns:
            result_df['out_date'] = None

        # 设置market信息（如果存在）
        if source_type == 'tushare' and 'market' in result_df.columns:
            # 保留market信息供其他地方使用
            pass

        return result_df

    @classmethod
    def validate_required_fields(cls, df: pd.DataFrame) -> tuple[bool, List[str]]:
        """
        验证必需字段是否存在且有效

        Args:
            df: 要验证的DataFrame

        Returns:
            (是否验证通过, 缺失或无效的字段列表)
        """
        required_fields = ['code', 'code_name', 'ipo_date']
        missing_fields = []
        invalid_fields = []

        for field in required_fields:
            if field not in df.columns:
                missing_fields.append(field)
            else:
                # 检查字段是否有效
                if field == 'code':
                    if df[field].isnull().any():
                        invalid_fields.append(f"{field}包含空值")
                elif field == 'code_name':
                    if df[field].isnull().any() or (df[field] == '').any():
                        invalid_fields.append(f"{field}包含空值或空字符串")
                elif field == 'ipo_date':
                    if df[field].isnull().any():
                        invalid_fields.append(f"{field}包含空值")

        all_issues = missing_fields + invalid_fields
        return len(all_issues) == 0, all_issues

    @classmethod
    def get_sql_columns_from_dataframe(cls, df: pd.DataFrame) -> List[tuple]:
        """
        从DataFrame获取SQL插入的列和值

        Args:
            df: 已标准化的DataFrame

        Returns:
            (列名列表, 值元组列表)
        """
        # 定义StockInfo表的字段顺序
        standard_fields = ['code', 'code_name', 'ipoDate', 'outDate', 'type', 'status', 'data_source']

        # 过滤出实际存在的字段
        available_fields = [field for field in standard_fields if field in df.columns]

        # 映射到数据库字段名
        db_field_mapping = {
            'code': 'code',
            'code_name': 'code_name',
            'ipo_date': 'ipoDate',
            'out_date': 'outDate',
            'type': 'type',
            'status': 'status',
            'data_source': 'data_source'
        }

        db_fields = [db_field_mapping[field] for field in available_fields]

        # 生成值元组列表
        values_list = []
        for _, row in df.iterrows():
            values = tuple(row[field] for field in available_fields)
            values_list.append(values)

        return db_fields, values_list