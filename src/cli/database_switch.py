#!/usr/bin/env python3
"""
数据库切换工具
用于在SQLite和PostgreSQL之间切换数据库类型
"""

import os
import re
import asyncio
import click
from pathlib import Path
from src.support.log.logger import logger


@click.group()
def cli():
    """数据库管理工具"""
    pass


@cli.command()
@click.option('--type',
              type=click.Choice(['sqlite', 'postgresql']),
              help='数据库类型 (sqlite/postgresql)',
              required=True)
def switch(type):
    """切换数据库类型"""
    try:
        config_path = Path('.env')

        # 读取现有配置
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                content = f.read()
        else:
            # 如果.env文件不存在，创建基础配置
            content = """# 环境变量配置文件
# 数据库类型选择 (sqlite/postgresql)
DATABASE_TYPE=postgresql

# SQLite 数据库配置 (当 DATABASE_TYPE=sqlite 时使用)
SQLITE_DB_PATH=./data/quantdb.sqlite

# PostgreSQL 数据库连接信息 (当 DATABASE_TYPE=postgresql 时使用)
DB_HOST=localhost
DB_PORT=5432
DB_NAME=quantdb
DB_USER=quant
DB_PASSWORD=your_secure_password_here

# 数据库连接池配置
DB_MAX_POOL_SIZE=15
DB_QUERY_TIMEOUT=60

# Baostock配置
BAOSTOCK_ENABLED=true

# 应用配置
APP_ENV=development
DEBUG=false
"""

        # 更新DATABASE_TYPE
        if 'DATABASE_TYPE=' in content:
            content = re.sub(r'DATABASE_TYPE=.*', f'DATABASE_TYPE={type}', content)
        else:
            content += f'\nDATABASE_TYPE={type}\n'

        # 写回配置文件
        with open(config_path, 'w', encoding='utf-8') as f:
            f.write(content)

        click.echo(f"✅ 已切换到 {type.upper()} 数据库模式")

        # 如果切换到SQLite，创建示例数据
        if type == 'sqlite':
            create_sample_sqlite()

        # 显示配置信息
        show_config_info(type)

    except Exception as e:
        click.echo(f"❌ 切换数据库失败: {str(e)}", err=True)


@cli.command()
def status():
    """显示当前数据库状态"""
    database_type = os.getenv('DATABASE_TYPE', 'postgresql')
    click.echo(f"当前数据库类型: {database_type.upper()}")

    if database_type == 'sqlite':
        sqlite_path = os.getenv('SQLITE_DB_PATH', './data/quantdb.sqlite')
        if os.path.exists(sqlite_path):
            file_size = os.path.getsize(sqlite_path)
            click.echo(f"SQLite数据库路径: {sqlite_path}")
            click.echo(f"数据库文件大小: {file_size / 1024:.2f} KB")
        else:
            click.echo(f"SQLite数据库文件不存在: {sqlite_path}")
            click.echo("💡 运行 'python -m src.cli.database_switch switch --type sqlite' 来创建数据库")

    elif database_type in ['postgresql', 'postgres']:
        host = os.getenv('DB_HOST', 'localhost')
        port = os.getenv('DB_PORT', '5432')
        dbname = os.getenv('DB_NAME', 'quantdb')
        user = os.getenv('DB_USER', 'quant')
        click.echo(f"PostgreSQL连接: {user}@{host}:{port}/{dbname}")


@cli.command()
def init():
    """初始化数据库"""
    database_type = os.getenv('DATABASE_TYPE', 'postgresql')

    if database_type == 'sqlite':
        create_sample_sqlite()
    else:
        click.echo("PostgreSQL数据库会自动初始化，请确保PostgreSQL服务已启动")


def create_sample_sqlite():
    """创建示例SQLite数据库"""
    try:
        click.echo("🔧 创建示例SQLite数据库...")

        # 运行异步初始化
        asyncio.run(_init_sqlite_database())

        click.echo("✅ SQLite数据库初始化完成")

    except Exception as e:
        click.echo(f"❌ SQLite数据库初始化失败: {str(e)}", err=True)


async def _init_sqlite_database():
    """异步初始化SQLite数据库"""
    from src.core.data.database_factory import get_db_adapter

    # 获取SQLite适配器
    adapter = get_db_adapter()

    # 初始化数据库和表结构
    await adapter.initialize()

    # 创建示例数据目录
    sqlite_path = os.getenv('SQLITE_DB_PATH', './data/quantdb.sqlite')
    data_dir = Path(sqlite_path).parent
    data_dir.mkdir(exist_ok=True)

    logger.info(f"SQLite数据库已创建: {sqlite_path}")


def show_config_info(database_type):
    """显示配置信息"""
    click.echo("\n📋 配置信息:")

    if database_type == 'sqlite':
        sqlite_path = os.getenv('SQLITE_DB_PATH', './data/quantdb.sqlite')
        click.echo(f"  - SQLite数据库路径: {sqlite_path}")
        click.echo("  - 优点: 零配置、快速体验、适合开发测试")
        click.echo("  - 注意: 不适合生产环境和大数据量场景")

    else:  # postgresql
        host = os.getenv('DB_HOST', 'localhost')
        port = os.getenv('DB_PORT', '5432')
        dbname = os.getenv('DB_NAME', 'quantdb')
        click.echo(f"  - PostgreSQL连接: {host}:{port}/{dbname}")
        click.echo("  - 优点: 高性能、适合生产环境、支持大数据量")
        click.echo("  - 注意: 需要额外安装和配置PostgreSQL服务")

    click.echo("\n🚀 快速开始:")
    click.echo("  streamlit run main.py")
    click.echo()


if __name__ == '__main__':
    cli()