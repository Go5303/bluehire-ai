
from datetime import datetime

from sqlalchemy import (
    String,
    Integer,
    BigInteger,
    Text,
    Boolean,
    DateTime,
    Index,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


# 工厂表
class Factory(Base):
    __tablename__ = "factories"

    id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True
    )

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    city: Mapped[str] = mapped_column(String(50), nullable=False)
    address: Mapped[str | None] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )


# 招聘岗位表
class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True
    )

    # 普通字段，不建立外键约束
    factory_id: Mapped[int] = mapped_column(BigInteger, nullable=False)

    title: Mapped[str] = mapped_column(String(100), nullable=False)
    city: Mapped[str] = mapped_column(String(50), nullable=False)

    salary_min: Mapped[int] = mapped_column(Integer, nullable=False)
    salary_max: Mapped[int] = mapped_column(Integer, nullable=False)

    has_night_shift: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )

    provide_accommodation: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )

    description: Mapped[str | None] = mapped_column(Text)

    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )

    __table_args__ = (
        Index("idx_factory_id", "factory_id"),
        Index("idx_city_active_salary", "city", "is_active", "salary_max"),
    )


# 报名记录表
class Application(Base):
    __tablename__ = "applications"

    id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True
    )

    user_id: Mapped[str] = mapped_column(String(64), nullable=False)
    job_id: Mapped[int] = mapped_column(BigInteger, nullable=False)

    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )

    __table_args__ = (
        UniqueConstraint("user_id", "job_id", name="uk_user_job"),
        Index("idx_job_id", "job_id"),
    )
