
from functools import lru_cache

from langchain_openai import OpenAIEmbeddings

from app.config import get_settings


@lru_cache(maxsize=1)
def get_embeddings() -> OpenAIEmbeddings:
    """获取阿里百炼Embedding客户端"""

    settings = get_settings()

    return OpenAIEmbeddings(
        model=settings.embedding_model,
        api_key=settings.dashscope_api_key.get_secret_value(),
        base_url=settings.dashscope_base_url,
        dimensions=1024, # 向量维度
        check_embedding_ctx_length=False,
    )