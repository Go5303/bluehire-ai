from charset_normalizer.md import lru_cache
from langchain_chroma import Chroma
from langchain_core.documents import Document
from pathlib import Path


from app.config import get_settings
from app.rag.embeddings import get_embeddings

# 1.初始化chroma
@lru_cache(maxsize=1)
def get_vector_store() -> Chroma:
    settings = get_settings()

    base_dir = Path(__file__).resolve().parents[2]
    persist_dir = Path(settings.chroma_persist_dir)

    if not persist_dir.is_absolute():
        persist_dir = base_dir / persist_dir

    return Chroma(
        collection_name="factory_policies",
        persist_directory=str(persist_dir),
        embedding_function=get_embeddings(),
    )

# 2.写入测试政策文档
def add_test_documents() -> None:
    vector_store = get_vector_store()

    documents = [
        Document(
            page_content="员工离职后，工资按照实际出勤天数结算，正常工资发放日为每月15日。",
            metadata={
                "factory_id": "1001",
                "category": "salary",
                "source": "factory_1001_salary",
            },
        ),
        Document(
            page_content="工厂提供免费员工宿舍，配备空调、热水器，宿舍为6人间。",
            metadata={
                "factory_id": "1001",
                "category": "dormitory",
                "source": "factory_1001_dormitory",
            },
        ),
        Document(
            page_content="入职需要携带身份证和银行卡，并按照工厂要求参加入职体检。",
            metadata={
                "factory_id": "1001",
                "category": "onboarding",
                "source": "factory_1001_onboarding",
            },
        ),
        Document(
            page_content="员工离职工资按照工厂当月结算周期核算，具体发薪日期需向招聘专员确认。",
            metadata={
                "factory_id": "1002",
                "category": "salary",
                "source": "factory_1002_salary",
            },
        ),
    ]

    ids = [
        "factory_1001_salary",
        "factory_1001_dormitory",
        "factory_1001_onboarding",
        "factory_1002_salary",
    ]

    vector_store.add_documents(
        documents=documents,
        ids=ids,
    )

    print("政策文档入库完成")

# 3.利用chroma实现检索
def search_policies(
        query: str,
        factory_id: str,
        k: int = 3,
) -> list[Document]:

    vector_store = get_vector_store()

    return vector_store.similarity_search(
        query=query,
        k=k,
        filter={"factory_id": factory_id},
    )

# 4.本地测试
if __name__ == "__main__":

    question = "这个厂干三天就不干了，工资还能拿到吗？"

    results = search_policies(
        query=question,
        factory_id="1001",
    )

    print("\n========== 检索结果 ==========")

    for index, doc in enumerate(results, start=1):
        print(f"\n第{index}条：")
        print("内容：", doc.page_content)
        print("元数据：", doc.metadata)