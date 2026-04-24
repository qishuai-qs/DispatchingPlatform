"""
应用配置管理模块
支持从环境变量和YAML配置文件加载配置
"""

import os
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import yaml
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseConfig(BaseSettings):
    """数据库配置"""

    model_config = SettingsConfigDict(env_prefix="DB_")

    url: str = Field(default="sqlite+aiosqlite:///./app.db", description="数据库连接URL")
    echo: bool = Field(default=False, description="是否打印SQL语句")
    pool_size: int = Field(default=5, description="连接池大小")
    max_overflow: int = Field(default=10, description="连接池溢出上限")


class JWTConfig(BaseSettings):
    """JWT认证配置"""

    model_config = SettingsConfigDict(env_prefix="JWT_")

    secret_key: str = Field(default="your-secret-key-change-in-production", description="JWT密钥")
    algorithm: str = Field(default="HS256", description="加密算法")
    access_token_expire_minutes: int = Field(default=30, description="访问令牌过期时间(分钟)")
    refresh_token_expire_days: int = Field(default=7, description="刷新令牌过期时间(天)")


class LogConfig(BaseSettings):
    """日志配置"""

    model_config = SettingsConfigDict(env_prefix="LOG_")

    level: str = Field(default="INFO", description="日志级别")
    format: str = Field(
        default="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        description="日志格式",
    )
    rotation: str = Field(default="20 MB", description="日志轮转大小")
    retention: str = Field(default="10 days", description="日志保留时间")


class SchedulerConfig(BaseSettings):
    """调度器配置"""

    model_config = SettingsConfigDict(env_prefix="SCHEDULER_")

    enabled: bool = Field(default=True, description="是否启用调度器")
    timezone: str = Field(default="Asia/Shanghai", description="时区")
    max_workers: int = Field(default=10, description="最大工作线程数")


class AppSettings(BaseSettings):
    """应用主配置类"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # 应用基本信息
    app_name: str = Field(default="qs-service", description="应用名称")
    app_version: str = Field(default="0.1.0", description="应用版本")
    debug: bool = Field(default=False, description="调试模式")
    env: str = Field(default="development", description="运行环境")

    # 服务器配置
    host: str = Field(default="0.0.0.0", description="服务器监听地址")
    port: int = Field(default=8000, description="服务器监听端口")

    # CORS配置
    cors_origins: List[str] = Field(
        default=["*"],
        description="允许的跨域来源",
    )

    # 子配置
    db: DatabaseConfig = Field(default_factory=DatabaseConfig)
    jwt: JWTConfig = Field(default_factory=JWTConfig)
    log: LogConfig = Field(default_factory=LogConfig)
    scheduler: SchedulerConfig = Field(default_factory=SchedulerConfig)

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        """解析CORS来源，支持字符串逗号分隔或列表"""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    @property
    def is_development(self) -> bool:
        """是否为开发环境"""
        return self.env.lower() in ("development", "dev", "local")

    @property
    def is_production(self) -> bool:
        """是否为生产环境"""
        return self.env.lower() in ("production", "prod")


def load_yaml_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    从YAML文件加载配置

    Args:
        config_path: 配置文件路径，默认查找 config/app.yaml

    Returns:
        配置字典
    """
    if config_path is None:
        # 查找默认配置文件
        possible_paths = [
            Path("config/app.yaml"),
            Path("config/app.yml"),
            Path("app.yaml"),
            Path("app.yml"),
        ]
        for path in possible_paths:
            if path.exists():
                config_path = str(path)
                break

    if config_path and Path(config_path).exists():
        with open(config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}

    return {}


@lru_cache()
def get_settings() -> AppSettings:
    """
    获取应用配置（单例模式）

    优先级：环境变量 > YAML配置 > 默认值
    """
    # 先加载YAML配置
    yaml_config = load_yaml_config()

    # 从YAML中提取配置
    config_dict = {
        "app_name": yaml_config.get("app", {}).get("name", "qs-service"),
        "app_version": yaml_config.get("app", {}).get("version", "0.1.0"),
        "debug": yaml_config.get("app", {}).get("debug", False),
        "env": yaml_config.get("app", {}).get("env", "development"),
        "host": yaml_config.get("server", {}).get("host", "0.0.0.0"),
        "port": yaml_config.get("server", {}).get("port", 8000),
        "cors_origins": yaml_config.get("server", {}).get("cors", {}).get("origins", ["*"]),
    }

    # 数据库配置
    if "database" in yaml_config:
        db_config = yaml_config["database"]
        config_dict["db"] = {
            "url": db_config.get("url", "sqlite+aiosqlite:///./app.db"),
            "echo": db_config.get("echo", False),
            "pool_size": db_config.get("pool_size", 5),
            "max_overflow": db_config.get("max_overflow", 10),
        }

    # JWT配置
    if "jwt" in yaml_config:
        jwt_config = yaml_config["jwt"]
        config_dict["jwt"] = {
            "secret_key": jwt_config.get("secret_key", "your-secret-key"),
            "algorithm": jwt_config.get("algorithm", "HS256"),
            "access_token_expire_minutes": jwt_config.get("access_token_expire_minutes", 30),
            "refresh_token_expire_days": jwt_config.get("refresh_token_expire_days", 7),
        }

    # 日志配置
    if "logging" in yaml_config:
        log_config = yaml_config["logging"]
        config_dict["log"] = {
            "level": log_config.get("level", "INFO"),
            "rotation": log_config.get("rotation", "20 MB"),
            "retention": log_config.get("retention", "10 days"),
        }

    # 调度器配置
    if "scheduler" in yaml_config:
        scheduler_config = yaml_config["scheduler"]
        config_dict["scheduler"] = {
            "enabled": scheduler_config.get("enabled", True),
            "timezone": scheduler_config.get("timezone", "Asia/Shanghai"),
            "max_workers": scheduler_config.get("max_workers", 10),
        }

    # 使用环境变量覆盖（pydantic-settings会自动处理）
    return AppSettings(**config_dict)


# 全局配置实例
settings = get_settings()
