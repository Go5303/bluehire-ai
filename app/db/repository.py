
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.schemas.job import JobSearch, JobResponse

# 查找相关工作
def search_jobs(
    db: Session,
    filters: JobSearch,
) -> list[JobResponse]:
    """根据条件查询招聘岗位"""

    sql = """
        SELECT
            j.id,
            j.factory_id,
            j.title,
            j.city,
            j.salary_min,
            j.salary_max,
            j.has_night_shift,
            j.provide_accommodation,
            j.description,
            j.is_active,
            f.name AS factory_name
        FROM jobs AS j
        LEFT JOIN factories AS f
            ON j.factory_id = f.id
        WHERE j.is_active = 1
    """

    params = {}

    # 城市筛选
    if filters.city is not None:
        sql += " AND j.city = :city"
        params["city"] = filters.city

    # 薪资筛选
    if filters.min_salary is not None:
        sql += " AND j.salary_max >= :min_salary"
        params["min_salary"] = filters.min_salary

    # 夜班筛选
    if filters.has_night_shift is not None:
        sql += " AND j.has_night_shift = :has_night_shift"
        params["has_night_shift"] = filters.has_night_shift

    # 住宿筛选
    if filters.provide_accommodation is not None:
        sql += (
            " AND j.provide_accommodation = "
            ":provide_accommodation"
        )
        params["provide_accommodation"] = (
            filters.provide_accommodation
        )

    sql += " ORDER BY j.id DESC LIMIT :limit"
    params["limit"] = filters.limit

    # 执行SQL，获得字典式结果
    rows = db.execute(
        text(sql),
        params,
    ).mappings().all()

    # 转换为Pydantic模型
    result = []
    for row in rows:
        data = dict(row)
        job = JobResponse.model_validate(data)
        result.append(job)
    return result
