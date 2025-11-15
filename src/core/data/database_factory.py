import os
from typing import Optional
from src.support.log.logger import logger
from .database_adapter import DatabaseAdapter
from .sqlite_adapter import SQLiteAdapter
from .postgresql_adapter import PostgreSQLAdapter


class DatabaseFactory:
    """数据库工厂类，负责根据配置创建相应的数据库适配器"""

    @staticmethod
    def create_adapter() -> DatabaseAdapter:
        """
        根据环境变量创建数据库适配器

        Returns:
            DatabaseAdapter: 数据库适配器实例
        """
        database_type = os.getenv('DATABASE_TYPE', 'postgresql').lower()

        try:
            if database_type == 'sqlite':
                sqlite_path = os.getenv('SQLITE_DB_PATH', './data/quantdb.sqlite')
                logger.info(f"创建SQLite适配器，数据库路径: {sqlite_path}")
                return SQLiteAdapter(sqlite_path)

            elif database_type in ['postgresql', 'postgres']:
                logger.info("创建PostgreSQL适配器")
                return PostgreSQLAdapter()

            else:
                raise ValueError(f"不支持的数据库类型: {database_type}")

        except Exception as e:
            logger.error(f"创建数据库适配器失败: {str(e)}")
            raise


def get_db_adapter() -> DatabaseAdapter:
    """
    获取数据库适配器实例（带缓存的工厂函数）

    Returns:
        DatabaseAdapter: 数据库适配器实例
    """
    return DatabaseFactory.create_adapter()


def get_database_type() -> str:
    """
    获取当前配置的数据库类型

    Returns:
        str: 数据库类型 ('sqlite' 或 'postgresql')
    """
    return os.getenv('DATABASE_TYPE', 'postgresql').lower()


def is_sqlite_mode() -> bool:
    """
    检查是否为SQLite模式

    Returns:
        bool: 是否为SQLite模式
    """
    return get_database_type() == 'sqlite'


def is_postgresql_mode() -> bool:
    """
    检查是否为PostgreSQL模式

    Returns:
        bool: 是否为PostgreSQL模式
    """
    return get_database_type() in ['postgresql', 'postgres']