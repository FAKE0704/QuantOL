"""添加 BacktestTasks 表的迁移脚本"""
import asyncio
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.data.database_factory import get_db_adapter
from src.support.log.logger import logger


async def migrate():
    """创建 BacktestTasks 表（如果不存在）"""
    try:
        # 获取数据库适配器
        db = get_db_adapter()
        await db.initialize()

        logger.info("开始迁移：检查 BacktestTasks 表是否存在...")

        # 检查表是否存在
        async with db.pool as conn:
            cursor = await conn.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name='BacktestTasks'
            """)
            result = await cursor.fetchone()

            if result:
                logger.info("✅ BacktestTasks 表已存在，无需迁移")
                return

            logger.info("🔨 BacktestTasks 表不存在，开始创建...")

            # 创建 BacktestTasks 表
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS BacktestTasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    backtest_id TEXT UNIQUE NOT NULL,
                    user_id INTEGER NOT NULL,
                    name TEXT,
                    status TEXT NOT NULL,
                    progress REAL DEFAULT 0,
                    current_time TEXT,
                    config TEXT NOT NULL,
                    result_summary TEXT,
                    error_message TEXT,
                    log_file_path TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    started_at TEXT,
                    completed_at TEXT
                )
            """)

            # 创建索引
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_backtest_tasks_user_id
                ON BacktestTasks(user_id)
            """)

            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_backtest_tasks_status
                ON BacktestTasks(status)
            """)

            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_backtest_tasks_created_at
                ON BacktestTasks(created_at DESC)
            """)

            logger.info("✅ BacktestTasks 表创建成功！")
            logger.info("🎉 迁移完成！")

    except Exception as e:
        logger.error(f"❌ 迁移失败: {e}")
        import traceback
        logger.error(f"详细错误: {traceback.format_exc()}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(migrate())
