from functools import lru_cache
from pathlib import Path

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

# 项目根目录
BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """BlueHire AI 配置管理"""

    # DeepSeek LLM
    deepseek_api_key: SecretStr
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-chat"

    # 阿里云百炼 Embedding 文本向量化
    dashscope_api_key: SecretStr
    dashscope_base_url: str = (
        "https://dashscope.aliyuncs.com/compatible-mode/v1"
    )
    embedding_model: str = "text-embedding-v4"

    # SQLite
    database_url: str = "sqlite:///./data/bluehire.db"

    # Chroma 向量数据看
    chroma_persist_dir: str = "./data/chroma"

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """获取并缓存配置对象"""
    return Settings()