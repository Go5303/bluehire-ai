import json

from langchain_core.tools import tool

from app.rag.vector_store import search_policies

@tool
def retrieve_policy_tool(
        query: str,
        factory_id: str,
        k: int = 3
) -> str:
    """查询指定工厂的招聘、入职及员工管理政策。

    当用户询问工厂的工资发放、离职结算、
    宿舍、体检、入职材料等政策时使用本工具。

    Args:
        query: 用户想咨询的具体政策问题。
        factory_id: 工厂ID，必须明确对应的工厂。
        k: 最多检索的文档数量，默认3条。
    """
    if not factory_id.strip():
        return json.dumps(
            {"error": "查询问题不能为空"},
            ensure_ascii=False,
        )

    # 1.检索Chroma向量数据库
    documents = search_policies(
        query=query,
        factory_id=factory_id,
        k=max(1, min(k, 5))
    )

    # 2.讲Document转换为普通字典
    data = [
        {
            "content": doc.page_content,
            "metadata": doc.metadata,
        }
        for doc in documents
    ]

    # 3.返回JSON字符串
    return json.dumps(
        {
            "factory_id": factory_id,
            "results": data,
            "count": len(data),
        },
        ensure_ascii=False,
    )





















