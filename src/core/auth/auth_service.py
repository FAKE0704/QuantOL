"""
认证服务
整合JWT服务和用户管理，提供完整的认证功能
"""

from typing import Dict, Optional, Tuple
from .jwt_service import JWTService
from .user_manager import UserManager

class AuthService:
    """认证服务"""

    def __init__(self, db_adapter):
        """
        初始化认证服务

        Args:
            db_adapter: 数据库适配器
        """
        self.db = db_adapter
        self.jwt_service = JWTService()
        self.user_manager = UserManager(db_adapter)

    async def register(self, username: str, email: str, password: str) -> Tuple[bool, str]:
        """
        用户注册

        Args:
            username: 用户名
            email: 邮箱
            password: 密码

        Returns:
            (是否成功, 消息)
        """
        success, msg = await self.user_manager.create_user(username, email, password)
        return success, msg

    async def login(self, username_or_email: str, password: str) -> Tuple[Optional[Dict], str]:
        """
        用户登录

        Args:
            username_or_email: 用户名或邮箱
            password: 密码

        Returns:
            (用户信息, token), 失败时返回 (None, 错误信息)
        """
        # 验证用户
        user = await self.user_manager.authenticate_user(username_or_email, password)
        if not user:
            return None, "用户名或密码错误"

        # 生成Token
        token = self.jwt_service.generate_token(
            user_id=user['id'],
            username=user['username'],
            role=user['role']
        )

        # 返回用户信息和Token
        return {
            'user': user,
            'token': token
        }, "登录成功"

    async def verify_token(self, token: str) -> Optional[Dict]:
        """
        验证Token

        Args:
            token: JWT Token

        Returns:
            Token载荷信息，验证失败返回None
        """
        try:
            payload = self.jwt_service.verify_token(token)

            # 验证用户是否仍然有效
            user = await self.user_manager.get_user_by_id(payload['user_id'])
            if not user:
                return None

            return payload
        except:
            return None

    async def refresh_token(self, token: str) -> Optional[str]:
        """
        刷新Token

        Args:
            token: 旧Token

        Returns:
            新Token，失败返回None
        """
        try:
            new_token = self.jwt_service.refresh_token(token)
            return new_token
        except:
            return None

    async def logout(self, token: str) -> bool:
        """
        用户登出（可在此处实现Token黑名单）

        Args:
            token: JWT Token

        Returns:
            是否成功
        """
        # 简单实现：记录登出日志
        try:
            payload = self.jwt_service.verify_token(token)
            await self.user_manager.log_operation(
                payload['user_id'],
                "logout",
                "用户登出"
            )
            return True
        except:
            return False

    async def get_registration_status(self) -> Dict:
        """获取注册状态"""
        return await self.user_manager.get_registration_status()