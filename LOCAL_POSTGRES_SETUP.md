# 本地PostgreSQL安装和配置指南

## 概述
将项目的数据库支持从Docker PostgreSQL扩展到支持到本地安装的PostgreSQL，提高性能和稳定性，**避免由于docker拉取镜像不稳定导致无法使用的问题**。

## macOS安装步骤（使用Homebrew）

### 1. 安装PostgreSQL
```bash
# 更新Homebrew
brew update

# 安装PostgreSQL
brew install postgresql

# 启动PostgreSQL服务
brew services start postgresql

# 验证安装
psql --version
```

### 2. 创建数据库和用户

或者使用命令行方式：
```bash
# 创建数据库
createdb quantdb

# 创建用户并设置密码
createuser quant
psql -d postgres -c "ALTER USER quant PASSWORD 'quant123';"

# 授权
psql -d quantdb -c "GRANT ALL PRIVILEGES ON DATABASE quantdb TO quant;"
psql -d quantdb -c "ALTER USER quant CREATEDB;"
```

### 3. 验证连接
```bash
# 测试连接
psql -h localhost -U quant -d quantdb

# 或者
psql postgresql://quant:quant123@localhost:5432/quantdb
```

## Windows安装步骤

### 1. 下载并安装PostgreSQL
- 访问 [EnterpriseDB](https://www.enterprisedb.com/downloads/postgres-postgresql-downloads)
- 下载PostgreSQL Windows版本
- 运行安装程序，记住设置的超级用户密码

### 2. 使用pgAdmin创建数据库
1. 打开pgAdmin
2. 连接到本地PostgreSQL服务器
3. 右键点击"Databases" → "Create" → "Database"
4. 数据库名称：`quantdb`
5. 创建新用户：`quant`，密码：`quant123`

### 3. 使用命令行（可选）
```cmd
# 打开SQL Shell
psql -U postgres

# 创建数据库和用户
CREATE DATABASE quantdb;
CREATE USER quant WITH PASSWORD 'quant123';
GRANT ALL PRIVILEGES ON DATABASE quantdb TO quant;
```

## Linux安装步骤

### Ubuntu/Debian
```bash
# 更新包列表
sudo apt update

# 安装PostgreSQL
sudo apt install postgresql postgresql-contrib

# 启动服务
sudo systemctl start postgresql
sudo systemctl enable postgresql

# 创建数据库和用户
sudo -u postgres psql << EOF
CREATE DATABASE quantdb;
CREATE USER quant WITH PASSWORD 'quant123';
GRANT ALL PRIVILEGES ON DATABASE quantdb TO quant;
ALTER USER quant CREATEDB;
\q
EOF
```

### CentOS/RHEL
```bash
# 安装PostgreSQL
sudo yum install postgresql-server postgresql-contrib

# 初始化数据库
sudo postgresql-setup initdb

# 启动服务
sudo systemctl start postgresql
sudo systemctl enable postgresql

# 创建数据库和用户
sudo -u postgres psql << EOF
CREATE DATABASE quantdb;
CREATE USER quant WITH PASSWORD 'quant123';
GRANT ALL PRIVILEGES ON DATABASE quantdb TO quant;
ALTER USER quant CREATEDB;
\q
EOF
```

## 项目配置更新

### 1. 更新.env文件
将项目根目录下的`.env`文件修改为：

```bash
# 数据库配置 - 本地PostgreSQL
DB_HOST=localhost
DB_PORT=5432
DB_NAME=quantdb
DB_USER=quant
DB_PASSWORD=quant123

# 可选：使用完整连接字符串
DATABASE_URL=postgresql://quant:quant123@localhost:5432/quantdb

# 管理数据库配置
ADMIN_DB_NAME=quantdb

# 连接池配置
DB_MAX_POOL_SIZE=15
DB_QUERY_TIMEOUT=60
```

### 2. 验证项目连接
```bash
# 确保虚拟环境激活
source .venvMac/bin/activate  # macOS/Linux
# 或
.venvWindows\Scripts\activate  # Windows

# 运行项目测试
python test_single_rule.py
```

## 常用PostgreSQL命令

### 服务管理
```bash
# macOS (Homebrew)
brew services start postgresql
brew services stop postgresql
brew services restart postgresql

# Linux (systemd)
sudo systemctl start postgresql
sudo systemctl stop postgresql
sudo systemctl restart postgresql

# Windows
# 通过服务管理器或pgAdmin控制
```

### 数据库操作
```bash
# 连接到数据库
psql -h localhost -U quant -d quantdb

# 列出所有数据库
\l

# 切换数据库
\c quantdb

# 列出所有表
\dt

# 查看表结构
\d StockData

# 退出
\q
```

### 备份和恢复
```bash
# 备份数据库
pg_dump -h localhost -U quant -d quantdb > backup.sql

# 恢复数据库
psql -h localhost -U quant -d quantdb < backup.sql

# 备份特定表
pg_dump -h localhost -U quant -d quantdb -t StockData > stockdata_backup.sql
```

## 性能优化建议

### 1. PostgreSQL配置优化
编辑 `postgresql.conf` 文件：
```bash
# 查找配置文件位置
psql -c 'SHOW config_file;'

# 主要优化参数
shared_buffers = 256MB
effective_cache_size = 1GB
maintenance_work_mem = 64MB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
random_page_cost = 1.1
effective_io_concurrency = 200
```

### 2. 连接池优化
在项目的`.env`文件中调整：
```bash
DB_MAX_POOL_SIZE=20
DB_QUERY_TIMEOUT=120
```

## 故障排除

### 1. 连接失败
```bash
# 检查PostgreSQL服务状态
brew services list | grep postgresql  # macOS
sudo systemctl status postgresql      # Linux

# 检查端口占用
netstat -an | grep 5432

# 查看PostgreSQL日志
tail -f /usr/local/var/log/postgres.log  # macOS
tail -f /var/log/postgresql/postgresql-main.log  # Linux
```

### 2. 权限问题
```bash
# 重新授权
psql -d quantdb -c "GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO quant;"
psql -d quantdb -c "GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO quant;"
```

### 3. 端口冲突
如果5432端口被占用，可以修改端口：
```bash
# 修改postgresql.conf中的port设置
port = 5433

# 更新项目.env文件
DB_PORT=5433
```

## 迁移Docker数据（可选）

如果需要将现有Docker数据库中的数据迁移到本地PostgreSQL：

```bash
# 1. 从Docker容器导出数据
docker exec postgres pg_dump -U quant quantdb > docker_data.sql

# 2. 导入到本地PostgreSQL
psql -h localhost -U quant -d quantdb < docker_data.sql
```

## 完成验证

安装完成后，运行以下命令验证：

```bash
# 1. 测试数据库连接
python -c "
from src.core.data.database import get_db_manager
import asyncio
async def test():
    db = get_db_manager()
    await db.initialize()
    print('数据库连接成功!')
asyncio.run(test())
"

# 2. 运行项目
streamlit run main.py
```

成功连接后，你就可以完全脱离Docker使用本地PostgreSQL了！
