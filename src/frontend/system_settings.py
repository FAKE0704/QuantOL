"""
系统设置页面
整合数据库设置和数据源配置
"""

import sys
import streamlit as st
import os
from pathlib import Path
from src.core.data.database_factory import get_database_type, is_sqlite_mode, is_postgresql_mode
from src.support.log.logger import logger
import asyncio


def show_system_settings_page():
    """显示系统设置页面"""
    st.title("⚙️ 系统设置")

    # 创建标签页
    tab1, tab2, tab3 = st.tabs(["🗄️ 数据库设置", "📊 数据源配置", "🔧 系统信息"])

    with tab1:
        show_database_settings()

    with tab2:
        show_data_source_settings()

    with tab3:
        show_system_info()


def show_database_settings():
    """显示数据库设置标签页"""
    st.subheader("🗄️ 数据库配置")

    # 添加简化说明
    st.info("""
    📌 **使用提示**：
    - **SQLite模式**: 零配置，自动创建本地数据库文件，适合快速体验和学习
    - **PostgreSQL模式**: 高性能，需要手动安装和配置数据库服务，适合生产环境
    """)

    # 显示当前数据库状态
    show_current_database_status()

    st.divider()

    # 数据库类型切换
    st.subheader("🔄 数据库类型切换")

    current_type = get_database_type()

    col1, col2 = st.columns(2)

    with col1:
        is_sqlite = is_sqlite_mode()
        if st.button("🗄️ 切换到 SQLite",
                    disabled=is_sqlite,
                    help="零配置，自动使用本地数据库文件",
                    use_container_width=True):
            switch_to_sqlite()

    with col2:
        is_pg = is_postgresql_mode()
        if st.button("🐘 切换到 PostgreSQL",
                    disabled=is_pg,
                    help="高性能，需要额外配置数据库服务",
                    use_container_width=True):
            switch_to_postgresql()

    st.divider()

    # 数据库配置信息
    st.subheader("⚙️ 数据库配置信息")

    if is_sqlite_mode():
        show_sqlite_config()
    else:
        show_postgresql_config()

    st.divider()

    # 数据库管理功能
    st.subheader("🛠️ 数据库管理")

    if is_sqlite_mode():
        show_sqlite_management()
    else:
        show_postgresql_management()


def show_data_source_settings():
    """显示数据源配置标签页"""
    st.subheader("📊 数据源配置")

    # 获取当前使用的数据源（优先从session_state获取，然后是环境变量，最后是默认值）
    if 'current_data_source' not in st.session_state:
        st.session_state.current_data_source = os.getenv('SELECTED_DATA_SOURCE', 'Baostock')

    current_source = st.session_state.current_data_source
    st.markdown(f"**当前使用的数据源：** **{current_source}**")

    st.divider()

    # 数据源选择
    st.write("**选择数据源：**")

    # 支持的数据源列表
    available_sources = ['Baostock', 'Tushare']

    col1, col2 = st.columns([3, 1])
    with col1:
        selected_source = st.selectbox(
            "数据源",
            options=available_sources,
            index=available_sources.index(current_source) if current_source in available_sources else 0,
            key="data_source_selector"
        )
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)  # 对齐按钮
        if st.button("使用", key="use_data_source", type="primary"):
            # 更新session_state
            st.session_state.current_data_source = selected_source
            # 保存到环境变量
            os.environ['SELECTED_DATA_SOURCE'] = selected_source
            st.success(f"已切换到 {selected_source}")
            # 刷新界面以更新显示
            st.rerun()

    # 配置选中的数据源
    st.divider()
    st.write("**数据源配置：**")
    _show_data_source_config(selected_source)




def _show_data_source_config(source_name):
    """显示数据源配置"""
    # 使用Streamlit原生组件
    with st.container():
        st.subheader(f"{source_name}")

        if source_name == "Tushare":
            current_token = os.getenv('TUSHARE_TOKEN', '')

            st.write("**API Token配置**")
            col1, col2 = st.columns([3, 1])

            with col1:
                new_token = st.text_input(
                    "API Token",
                    value=current_token,
                    type="password",
                    key="tushare_token",
                    help="在 https://tushare.pro 注册获取Token"
                )

            with col2:
                if st.button("保存", key="save_tushare_token"):
                    if new_token:
                        os.environ['TUSHARE_TOKEN'] = new_token
                        st.success("Token已保存")
                        st.rerun()
                    else:
                        st.error("请输入Token")

            # 只在有Token时显示状态
            if current_token:
                st.caption(f"已配置: ***{current_token[-8:]}***")

            st.info("💡 登录[TUSHARE](https://tushare.pro/register?reg=693641)以获取TUSHARE API token")

        elif source_name == "Baostock":
            st.info("💡 Baostock是免费数据源，无需配置Token，适合作为默认数据源")

        else:
            st.info(f"💡 {source_name} 数据源配置")




def show_system_info():
    """显示系统信息标签页"""
    st.subheader("🔧 系统信息")

    # 简单的系统信息
    st.info("""
    **智能量化交易平台**

    - 版本: 1.0.0
    - 支持的数据源: Tushare, Baostock
    - 数据库: SQLite / PostgreSQL

    如需技术支持，请联系开发团队。
    """)


# 复用原有的数据库相关函数
def show_current_database_status():
    """显示当前数据库状态"""
    current_type = get_database_type()

    if is_sqlite_mode():
        st.success(f"🟢 当前使用: SQLite 数据库")

        sqlite_path = os.getenv('SQLITE_DB_PATH', './data/quantdb.sqlite')
        if Path(sqlite_path).exists():
            file_size = Path(sqlite_path).stat().st_size / 1024
            st.info(f"📁 数据库路径: `{sqlite_path}`")
            st.info(f"💾 文件大小: {file_size:.2f} KB")
        else:
            st.warning(f"⚠️ 数据库文件不存在: `{sqlite_path}`")

            # 自动初始化SQLite数据库
            st.info("🔧 正在自动初始化SQLite数据库...")
            try:
                asyncio.run(_init_sqlite_database())
                st.success("✅ SQLite数据库初始化完成")
                st.experimental_rerun()
            except Exception as e:
                st.error(f"❌ 自动初始化失败: {str(e)}")

    else:
        st.success(f"🟢 当前使用: PostgreSQL 数据库")

        host = os.getenv('DB_HOST', 'localhost')
        port = os.getenv('DB_PORT', '5432')
        dbname = os.getenv('DB_NAME', 'quantdb')
        user = os.getenv('DB_USER', 'quant')

        st.info(f"🖥️ 连接信息: `{user}@{host}:{port}/{dbname}`")


def show_sqlite_config():
    """显示SQLite配置信息"""
    st.write("**SQLite 配置**")

    sqlite_path = os.getenv('SQLITE_DB_PATH', './data/quantdb.sqlite')
    st.info(f"📁 数据库文件路径: `{sqlite_path}`")
    st.caption("💡 提示：数据库文件路径已自动配置，无需手动设置")


def show_postgresql_config():
    """显示PostgreSQL配置信息"""
    st.write("**PostgreSQL 配置**")

    col1, col2 = st.columns(2)

    with col1:
        host = st.text_input("主机地址", value=os.getenv('DB_HOST', 'localhost'))
        port = st.text_input("端口", value=os.getenv('DB_PORT', '5432'))
        dbname = st.text_input("数据库名", value=os.getenv('DB_NAME', 'quantdb'))

    with col2:
        user = st.text_input("用户名", value=os.getenv('DB_USER', 'quant'))
        password = st.text_input("密码",
                                value=os.getenv('DB_PASSWORD', ''),
                                type="password")
        max_pool = st.text_input("连接池大小",
                                value=os.getenv('DB_MAX_POOL_SIZE', '15'))

    if st.button("保存PostgreSQL配置"):
        os.environ['DB_HOST'] = host
        os.environ['DB_PORT'] = port
        os.environ['DB_NAME'] = dbname
        os.environ['DB_USER'] = user
        os.environ['DB_PASSWORD'] = password
        os.environ['DB_MAX_POOL_SIZE'] = max_pool
        st.success("配置已保存")
        st.experimental_rerun()


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


def show_sqlite_management():
    """显示SQLite管理功能"""
    col1, col2 = st.columns(2)

    with col1:
        if st.button("🔄 重新初始化数据库",
                    help="删除现有数据库并重新创建",
                    use_container_width=True):
            with st.spinner("正在重新初始化数据库..."):
                try:
                    asyncio.run(reinit_sqlite_database())
                    st.success("数据库重新初始化完成")
                except Exception as e:
                    st.error(f"初始化失败: {str(e)}")

    with col2:
        if st.button("📁 打开数据库文件夹",
                    help="在文件管理器中打开数据库所在文件夹",
                    use_container_width=True):
            sqlite_path = Path(os.getenv('SQLITE_DB_PATH', './data/quantdb.sqlite'))
            if sqlite_path.exists():
                import subprocess
                import platform

                try:
                    if platform.system() == "Windows":
                        subprocess.run(['explorer', '/select,', str(sqlite_path)])
                    elif platform.system() == "Darwin":  # macOS
                        subprocess.run(['open', '-R', str(sqlite_path)])
                    else:  # Linux
                        subprocess.run(['xdg-open', str(sqlite_path.parent)])
                    st.success("已打开文件夹")
                except Exception as e:
                    st.error(f"无法打开文件夹: {str(e)}")
            else:
                st.error("数据库文件不存在")


def show_postgresql_management():
    """显示PostgreSQL管理功能"""
    col1, col2 = st.columns(2)

    with col1:
        if st.button("🔄 测试连接",
                    help="测试PostgreSQL数据库连接",
                    use_container_width=True):
            with st.spinner("正在测试连接..."):
                try:
                    result = asyncio.run(test_postgresql_connection())
                    if result:
                        st.success("✅ 数据库连接成功")
                    else:
                        st.error("❌ 数据库连接失败")
                except Exception as e:
                    st.error(f"连接测试失败: {str(e)}")

    with col2:
        if st.button("🐘 启动Docker PostgreSQL",
                    help="使用Docker启动PostgreSQL服务",
                    use_container_width=True):
            st.info("请手动运行以下命令启动Docker PostgreSQL:")
            st.code("docker-compose up -d")


async def reinit_sqlite_database():
    """重新初始化SQLite数据库"""
    sqlite_path = os.getenv('SQLITE_DB_PATH', './data/quantdb.sqlite')

    # 删除现有数据库文件
    if Path(sqlite_path).exists():
        Path(sqlite_path).unlink()

    # 重新创建数据库
    from src.core.data.database_factory import get_db_adapter
    adapter = get_db_adapter()
    await adapter.initialize()


async def test_postgresql_connection():
    """测试PostgreSQL连接"""
    try:
        from src.core.data.database_factory import get_db_adapter
        adapter = get_db_adapter()
        await adapter.initialize()
        return True
    except Exception as e:
        logger.error(f"PostgreSQL连接测试失败: {str(e)}")
        return False


def switch_to_sqlite():
    """切换到SQLite"""
    try:
        import subprocess
        import sys

        # 调用命令行工具切换数据库
        result = subprocess.run([
            sys.executable, "-m", "src.cli.database_switch",
            "switch", "--type", "sqlite"
        ], capture_output=True, text=True)

        if result.returncode == 0:
            # 更新当前进程的环境变量
            import os
            os.environ['DATABASE_TYPE'] = 'sqlite'

            # 清除可能的数据库缓存
            if 'db' in st.session_state:
                del st.session_state.db

            st.success("✅ 已切换到 SQLite 数据库")
            st.experimental_rerun()
        else:
            st.error(f"❌ 切换失败: {result.stderr}")

    except Exception as e:
        st.error(f"❌ 切换失败: {str(e)}")


def switch_to_postgresql():
    """切换到PostgreSQL"""
    try:
        import subprocess
        import sys

        # 调用命令行工具切换数据库
        result = subprocess.run([
            sys.executable, "-m", "src.cli.database_switch",
            "switch", "--type", "postgresql"
        ], capture_output=True, text=True)

        if result.returncode == 0:
            # 更新当前进程的环境变量
            import os
            os.environ['DATABASE_TYPE'] = 'postgresql'

            # 清除可能的数据库缓存
            if 'db' in st.session_state:
                del st.session_state.db

            st.success("✅ 已切换到 PostgreSQL 数据库")
            st.experimental_rerun()
        else:
            st.error(f"❌ 切换失败: {result.stderr}")

    except Exception as e:
        st.error(f"❌ 切换失败: {str(e)}")


def show_database_status_widget():
    """在侧边栏显示数据库状态小部件"""
    with st.sidebar:
        st.markdown("---")
        st.subheader("🔧 系统状态")

        # 确保获取最新的数据库类型
        current_type = get_database_type()

        if is_sqlite_mode():
            st.success(f"🗄️ SQLite")
            sqlite_path = os.getenv('SQLITE_DB_PATH', './data/quantdb.sqlite')
            if Path(sqlite_path).exists():
                file_size = Path(sqlite_path).stat().st_size / 1024
                st.caption(f"📁 {file_size:.1f} KB")
            else:
                st.warning("⚠️ 文件不存在")
        else:
            st.success(f"🐘 PostgreSQL")
            st.caption(f"🖥️ {os.getenv('DB_HOST', 'localhost')}")

        # 当前使用的数据源
        current_source = st.session_state.get('current_data_source', 'Baostock')
        st.caption(f"📊 数据源: {current_source}")

        if st.button("⚙️ 系统设置", key="system_settings_sidebar"):
            st.session_state.current_page = "系统设置"
            # 确保在切换页面时清除数据库缓存以强制重新初始化
            if 'db' in st.session_state:
                del st.session_state.db