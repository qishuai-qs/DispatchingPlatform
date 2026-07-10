"""
Elasticsearch 异步客户端管理模块
"""

from typing import Optional

from elasticsearch import AsyncElasticsearch

from app.core.config import settings
from app.utils.logger import get_logger

logger = get_logger("elasticsearch")

# 全局 ES 客户端实例（单例）
_es_client: Optional[AsyncElasticsearch] = None


def get_es_client() -> AsyncElasticsearch:
    """
    获取全局 AsyncElasticsearch 客户端实例

    Returns:
        AsyncElasticsearch 实例

    Raises:
        RuntimeError: 如果客户端未初始化
    """
    global _es_client
    if _es_client is None:
        raise RuntimeError("Elasticsearch client not initialized. Call init_es() first.")
    return _es_client


async def init_es() -> None:
    """
    初始化 Elasticsearch 异步客户端
    在应用启动时调用（lifespan）
    """
    global _es_client

    if not settings.es.enabled:
        logger.info("Elasticsearch is disabled, skipping initialization")
        return

    # 构建连接参数
    kwargs = {
        "hosts": settings.es.hosts,
        "request_timeout": 30,
        "retry_on_timeout": True,
        "max_retries": 3,
    }

    # 认证配置
    if settings.es.username and settings.es.password:
        kwargs["basic_auth"] = (settings.es.username, settings.es.password)

    _es_client = AsyncElasticsearch(**kwargs)

    # 验证连接
    try:
        info = await _es_client.info()
        logger.info(f"Elasticsearch connected: {info['version']['number']}")
    except Exception as e:
        logger.error(f"Elasticsearch connection failed: {e}")
        # 连接失败时不阻止应用启动，后续写入日志时会记录错误


async def close_es() -> None:
    """
    关闭 Elasticsearch 连接
    在应用关闭时调用（lifespan）
    """
    global _es_client
    if _es_client is not None:
        await _es_client.close()
        _es_client = None
        logger.info("Elasticsearch connection closed")