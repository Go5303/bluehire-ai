import json

from langchain_core.tools import tool
from langchain.tools import ToolRuntime
from langgraph.types import interrupt
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app.db.database import SessionLocal

def to_json(data: dict) -> str:
    return json.dumps(data, ensure_ascii=False)

@tool
def apply_job_tools(
        job_id: int,
        runtime: ToolRuntime,
) -> str:
    """为当前登录用户报名指定招聘岗位。

     仅在用户明确提出报名意愿时使用。
     job_id必须来自真实岗位查询结果。
     执行报名前必须通过人工确认。
    """

    #1. 从Graph运行上下文获取当前用户
    user_id = runtime.context.user_id

    if not user_id:
        return to_json({
            "success": False,
            "message": "无法识别当前用户",
        })

    if job_id <= 0:
        return to_json({
            "success": False,
            "message": "岗位ID不合法",
        })

    # 2. 检查岗位是否存在、是否还在招聘
    with SessionLocal() as db:
        job = db.execute(
            text("""
                 SELECT id, title, factory_id, is_active
                 FROM jobs
                 WHERE id = :job_id
                 """),
            {"job_id": job_id},
        ).mappings().first()

        if not job or not job["is_active"]:
            return to_json({
                "success": False,
                "message": "岗位不存在或已停止招聘",
            })

        # 已经报名过的岗位直接返回
        existing = db.execute(
            text("""
                 SELECT id, status
                 FROM applications
                 WHERE user_id = :user_id
                   AND job_id = :job_id
                 """),
            {
                "user_id": user_id,
                "job_id": job_id,
            },
        ).mappings().first()

    if existing:
        return to_json({
            "success": False,
            "message": "你已经报名过该岗位",
            "application_id": existing["id"],
            "status": existing["status"],
        })

    job_title = job["title"]
    factory_id = job["factory_id"]

    # 3. 暂停Graph，等待用户确认
    approved = interrupt({
        "type": "apply_job_confirmation",
        "message": "确认报名以下岗位吗？",
        "job_id": job_id,
        "job_title": job_title,
        "factory_id": factory_id,
    })

    # 4.用户取消，不写入mysql
    if approved is not True:
        return to_json({
            "success": False,
            "message": "用户已取消报名",
        })

    with SessionLocal() as db:
        try:
            # 恢复后再次检查岗位是否仍在招聘
            active = db.execute(
                text("""
                     SELECT is_active
                     FROM jobs
                     WHERE id = :job_id
                     """),
                {"job_id": job_id},
            ).scalar_one_or_none()

            if not active:
                return to_json({
                    "success": False,
                    "message": "该岗位目前已停止招聘",
                })
            result = db.execute(
                text("""
                    INSERT INTO applications
                        (user_id, job_id, status)
                    VALUES
                        (:user_id, :job_id, 'pending')
                """),
                {
                    "user_id": user_id,
                    "job_id": job_id,
                },
            )

            application_id = result.lastrowid
            db.commit()
            return to_json({
                "success": True,
                "message": "报名成功",
                "application_id": application_id,
                "job_id": job_id,
                "status": "pending",
            })

        except IntegrityError:
            db.rollback()
            return to_json({
                "success": False,
                "message": "该用户可能已报名过此岗位",
            })














