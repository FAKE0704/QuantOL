import os
from typing import Optional
from src.support.log.logger import logger
from .database_adapter import DatabaseAdapter
from .sqlite_adapter import SQLiteAdapter
from .postgresql_adapter import PostgreSQLAdapter


class DatabaseFactory:
    """数据库工厂类，负责根据配置创建相应的数据库适配器"""

    # 简单的单例缓存
    _adapter_instance: Optional[DatabaseAdapter] = None

    @classmethod
    def create_adapter(cls) -> DatabaseAdapter:
        """
        根据环境变量创建数据库适配器（单例模式）

        Returns:
            DatabaseAdapter: 数据库适配器实例
        """
        # 如果已有实例，直接返回
        if cls._adapter_instance is not None:
            logger.info("使用已存在的数据库适配器实例")
            return cls._adapter_instance

        database_type = os.getenv('DATABASE_TYPE', 'postgresql').lower()

        try:
            if database_type == 'sqlite':
                sqlite_path = os.getenv('SQLITE_DB_PATH', './data/quantdb.sqlite')
                logger.info(f"创建新的SQLite适配器，数据库路径: {sqlite_path}")
                cls._adapter_instance = SQLiteAdapter(sqlite_path)
                return cls._adapter_instance

            elif database_type in ['postgresql', 'postgres']:
                logger.info("创建新的PostgreSQL适配器")
                cls._adapter_instance = PostgreSQLAdapter()
                return cls._adapter_instance

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
    adapter = DatabaseFactory.create_adapter()

    # 如果是SQLite适配器，设置数据源管理器引用
    try:
        from .config.data_source_config import get_data_source_manager
        data_source_manager = get_data_source_manager()
        if hasattr(adapter, 'set_data_source_manager'):
            adapter.set_data_source_manager(data_source_manager)
    except ImportError:
        logger.warning("无法导入数据源管理器，使用默认数据源")

    return adapter


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