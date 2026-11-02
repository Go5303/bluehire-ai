
import json

from langchain_core.tools import tool

from app.db.database import SessionLocal
from app.db.repository import search_jobs
from app.schemas.job import JobSearch


@tool
def search_jobs_tool(
    city: str | None = None,
    min_salary: int | None = None,
    has_night_shift: bool | None = None,
    provide_accommodation: bool | None = None,
    limit: int = 10,
) -> str:
    """查询真实招聘岗位。

    根据城市、最低期望月薪、夜班要求和住宿要求
    从MySQL数据库中查找正在招聘的岗位。

    min_salary表示用户期望的最低薪资，
    筛选岗位薪资区间上限达到该数值的工作。
    """

    # 1. 使用Pydantic验证参数
    filters = JobSearch(
        city=city,
        min_salary=min_salary,
        has_night_shift=has_night_shift,
        provide_accommodation=provide_accommodation,
        limit=limit,
    )

    # 2. 查询MySQL
    with SessionLocal() as db:
        jobs = search_jobs(db, filters)

    # 3. 返回JSON字符串
    data = [job.model_dump() for job in jobs]

    return json.dumps(data, ensure_ascii=False)
