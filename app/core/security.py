"""
安全工具模块
提供密码加密、JWT Token生成和验证等功能
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    验证密码

    Args:
        plain_password: 明文密码
        hashed_password: 加密后的密码

    Returns:
        是否匹配
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    获取密码哈希值

    Args:
        password: 明文密码

    Returns:
        加密后的密码
    """
    return pwd_context.hash(password)


def create_access_token(
    subject: str,
    expires_delta: Optional[timedelta] = None,
    extra_claims: Optional[Dict[str, Any]] = None,
) -> str:
    """
    创建访问令牌

    Args:
        subject: 主题（通常是用户ID）
        expires_delta: 过期时间增量
        extra_claims: 额外声明

    Returns:
        JWT令牌字符串
    """
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.jwt.access_token_expire_minutes
        )

    to_encode = {
        "sub": subject,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "access",
    }

    if extra_claims:
        to_encode.update(extra_claims)

    encoded_jwt = jwt.encode(
        to_encode, settings.jwt.secret_key, algorithm=settings.jwt.algorithm
    )
    return encoded_jwt


def create_refresh_token(
    subject: str,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    创建刷新令牌

    Args:
        subject: 主题（通常是用户ID）
        expires_delta: 过期时间增量

    Returns:
        JWT令牌字符串
    """
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            days=settings.jwt.refresh_token_expire_days
        )

    to_encode = {
        "sub": subject,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "refresh",
    }

    encoded_jwt = jwt.encode(
        to_encode, settings.jwt.secret_key, algorithm=settings.jwt.algorithm
    )
    return encoded_jwt


def decode_token(token: str) -> Optional[Dict[str, Any]]:
    """
    解码JWT令牌

    Args:
        token: JWT令牌字符串

    Returns:
        解码后的载荷，失败返回None
    """
    try:
        payload = jwt.decode(
            token, settings.jwt.secret_key, algorithms=[settings.jwt.algorithm]
        )
        return payload
    except JWTError:
        return None


def verify_token(token: str, token_type: str = "access") -> Optional[Dict[str, Any]]:
    """
    验证JWT令牌

    Args:
        token: JWT令牌字符串
        token_type: 令牌类型（access/refresh）

    Returns:
        验证通过的载荷，失败返回None
    """
    payload = decode_token(token)
    if payload is None:
        return None

    # 检查令牌类型
    if payload.get("type") != token_type:
        return None

    # 检查过期时间
    exp = payload.get("exp")
    if exp is None:
        return None

    if datetime.now(timezone.utc).timestamp() > exp:
        return None

    return payload


def get_token_subject(token: str) -> Optional[str]:
    """
    从令牌中获取主题（用户ID）

    Args:
        token: JWT令牌字符串

    Returns:
        用户ID，失败返回None
    """
    payload = decode_token(token)
    if payload:
        return payload.get("sub")
    return None
