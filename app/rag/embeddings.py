
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


if __name__ == "__main__":
    embeddings = get_embeddings()

    # 1. 单条文本向量化
    query = "工厂干三天离职，工资怎么算？"

    query_vector = embeddings.embed_query(query)

    print("问题向量维度：", len(query_vector))

    # 2. 多条文档向量化
    documents = [
        "员工离职工资按实际出勤天数结算。",
        "工厂提供免费宿舍，宿舍配有空调。",
        "员工入职需要携带身份证和银行卡。",
    ]

    document_vectors = embeddings.embed_documents(documents)

    print("文档数量：", len(document_vectors))

    for i, vector in enumerate(document_vectors):
        print(f"第{i + 1}条文档向量维度：{len(vector)}")
