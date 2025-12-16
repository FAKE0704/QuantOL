"""
用户管理服务（简化版）
负责用户的创建、验证和测试名额控制
"""

import bcrypt
import os
from datetime import datetime
from typing import Dict, Optional, Tuple

class UserManager:
    """用户管理服务"""

    def __init__(self, db_adapter):
        """
        初始化用户管理器

        Args:
            db_adapter: 数据库适配器实例
        """
        self.db = db_adapter
        self.MAX_USERS = int(os.getenv("MAX_USERS", "100"))  # 最大测试用户数
        self._init_user_tables()

    async def _init_user_tables(self):
        """初始化用户相关数据表"""
        # 创建用户表
        await self.db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                role VARCHAR(20) DEFAULT 'user',
                status VARCHAR(20) DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP
            )
        """)

        # 创建用户会话表
        await self.db.execute("""
            CREATE TABLE IF NOT EXISTS user_sessions (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id),
                token_hash VARCHAR(255) NOT NULL,
                expires_at TIMESTAMP NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 创建操作日志表
        await self.db.execute("""
            CREATE TABLE IF NOT EXISTS user_operation_logs (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id),
                operation_type VARCHAR(50) NOT NULL,
                operation_detail TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 创建默认管理员用户（如果不存在）
        await self._create_default_admin()

    async def _create_default_admin(self):
        """创建默认管理员用户"""
        admin_email = os.getenv("ADMIN_EMAIL", "admin@quantol.com")
        admin_password = os.getenv("ADMIN_PASSWORD", "admin123456")

        # 检查管理员是否存在
        admin_exists = await self.db.fetch_one(
            "SELECT id FROM users WHERE role = 'admin' LIMIT 1"
        )

        if not admin_exists:
            # 创建管理员
            password_hash = bcrypt.hashpw(admin_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            await self.db.execute("""
                INSERT INTO users (username, email, password_hash, role)
                VALUES (%s, %s, %s, %s)
            """, ("admin", admin_email, password_hash, "admin"))
            print(f"默认管理员已创建: {admin_email} / {admin_password}")

    def _hash_password(self, password: str) -> str:
        """密码哈希加密"""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

    def _verify_password(self, password: str, password_hash: str) -> bool:
        """验证密码"""
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))

    def _validate_password(self, password: str) -> Tuple[bool, str]:
        """验证密码强度"""
        if len(password) < 6:
            return False, "密码长度至少6位"

        return True, "密码强度合格"

    async def can_register(self) -> Tuple[bool, str]:
        """检查是否可以注册新用户"""
        # 查询当前用户总数
        result = await self.db.fetch_one("SELECT COUNT(*) as count FROM users")
        current_count = result['count']

        if current_count >= self.MAX_USERS:
            return False, f"测试名额已满（{self.MAX_USERS}/{self.MAX_USERS}），请等待下一批开放"

        remaining = self.MAX_USERS - current_count
        return True, f"当前剩余名额: {remaining}"

    async def get_registration_status(self) -> Dict:
        """获取注册状态信息"""
        result = await self.db.fetch_one("SELECT COUNT(*) as count FROM users")
        current_count = result['count']

        return {
            'max_users': self.MAX_USERS,
            'registered': current_count,
            'remaining': max(0, self.MAX_USERS - current_count),
            'is_full': current_count >= self.MAX_USERS
        }

    async def create_user(self, username: str, email: str, password: str) -> Tuple[bool, str]:
        """
        创建新用户

        Args:
            username: 用户名
            email: 邮箱
            password: 密码

        Returns:
            (是否成功, 消息)
        """
        # 检查是否还有名额
        can_register, msg = await self.can_register()
        if not can_register:
            return False, msg

        # 验证密码强度
        valid, msg = self._validate_password(password)
        if not valid:
            return False, msg

        # 检查用户名是否已存在
        existing = await self.db.fetch_one(
            "SELECT id FROM users WHERE username = %s OR email = %s",
            (username, email)
        )
        if existing:
            return False, "用户名或邮箱已存在"

        # 密码加密
        password_hash = self._hash_password(password)

        # 创建用户
        await self.db.execute("""
            INSERT INTO users (username, email, password_hash)
            VALUES (%s, %s, %s)
        """, (username, email, password_hash))

        # 记录日志
        await self.log_operation(None, "user_register", f"新用户注册: {username}")

        return True, "注册成功！"

    async def authenticate_user(self, username_or_email: str, password: str) -> Optional[Dict]:
        """
        验证用户登录

        Args:
            username_or_email: 用户名或邮箱
            password: 密码

        Returns:
            用户信息字典，验证失败返回None
        """
        # 查询用户
        user = await self.db.fetch_one(
            "SELECT * FROM users WHERE (username = %s OR email = %s) AND status = 'active'",
            (username_or_email, username_or_email)
        )

        if not user:
            return None

        # 验证密码
        if not self._verify_password(password, user['password_hash']):
            return None

        # 更新最后登录时间
        await self.db.execute(
            "UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = %s",
            (user['id'],)
        )

        # 记录登录日志
        await self.log_operation(user['id'], "login", "用户登录")

        return {
            'id': user['id'],
            'username': user['username'],
            'email': user['email'],
            'role': user['role']
        }

    async def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        """根据ID获取用户信息"""
        user = await self.db.fetch_one(
            "SELECT id, username, email, role, created_at FROM users WHERE id = %s",
            (user_id,)
        )
        return user

    async def log_operation(self, user_id: Optional[int], operation_type: str, detail: str = None):
        """记录用户操作日志"""
        await self.db.execute("""
            INSERT INTO user_operation_logs (user_id, operation_type, operation_detail)
            VALUES (%s, %s, %s)
        """, (user_id, operation_type, detail))