"""
JWT Token 服务
负责生成、验证和管理 JWT Token
"""

import jwt
import os
from datetime import datetime, timedelta
from typing import Dict, Optional

class JWTService:
    """JWT Token 管理服务"""

    def __init__(self):
        """初始化JWT服务"""
        self.secret_key = os.getenv("JWT_SECRET_KEY", "quantol-default-secret-key-change-in-production")
        self.algorithm = "HS256"
        self.token_expiry = int(os.getenv("TOKEN_EXPIRY_HOURS", "24"))  # 默认24小时

    def generate_token(self, user_id: int, username: str, role: str = "user") -> str:
        """
        生成JWT Token

        Args:
            user_id: 用户ID
            username: 用户名
            role: 用户角色

        Returns:
            JWT Token字符串
        """
        now = datetime.utcnow()
        payload = {
            'user_id': user_id,
            'username': username,
            'role': role,
            'iat': now,
            'exp': now + timedelta(hours=self.token_expiry)
        }

        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def verify_token(self, token: str) -> Dict:
        """
        验证JWT Token

        Args:
            token: JWT Token字符串

        Returns:
            Token载荷信息

        Raises:
            jwt.ExpiredSignatureError: Token已过期
            jwt.InvalidTokenError: Token无效
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            raise jwt.ExpiredSignatureError("Token已过期")
        except jwt.InvalidTokenError as e:
            raise jwt.InvalidTokenError(f"无效Token: {str(e)}")

    def refresh_token(self, token: str) -> str:
        """
        刷新Token（生成新的Token）

        Args:
            token: 旧的JWT Token

        Returns:
            新的JWT Token
        """
        payload = self.verify_token(token)

        # 生成新Token
        return self.generate_token(
            payload['user_id'],
            payload['username'],
            payload.get('role', 'user')
        )

    def get_token_remaining_time(self, token: str) -> int:
        """
        获取Token剩余有效时间（秒）

        Args:
            token: JWT Token

        Returns:
            剩余时间（秒），如果Token无效返回0
        """
        try:
            payload = self.verify_token(token)
            exp = payload.get('exp', 0)
            now = datetime.utcnow().timestamp()
            remaining = exp - now
            return max(0, int(remaining))
        except:
            return 0