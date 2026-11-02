
from pydantic import BaseModel, Field, ConfigDict, model_validator


class JobSearch(BaseModel):
    """岗位查询参数"""

    city: str | None = Field(
        default=None,
        description="求职城市，例如苏州",
    )

    min_salary: int | None = Field(
        default=None,
        ge=0,
        description="期望最低月薪，单位元",
    )

    has_night_shift: bool | None = Field(
        default=None,
        description="是否包含夜班；False表示只接受无夜班岗位",
    )

    provide_accommodation: bool | None = Field(
        default=None,
        description="是否提供住宿；True表示只查询提供住宿的岗位",
    )

    limit: int = Field(default=10, ge=1, le=50)


class JobCreate(BaseModel):
    """新增岗位参数"""

    factory_id: int = Field(gt=0)
    title: str = Field(min_length=1, max_length=100)
    city: str = Field(min_length=1, max_length=50)

    salary_min: int = Field(ge=0)
    salary_max: int = Field(ge=0)

    has_night_shift: bool = False
    provide_accommodation: bool = False
    description: str | None = None

    @model_validator(mode="after")
    def validate_salary(self):
        if self.salary_max < self.salary_min:
            raise ValueError("最高薪资不能低于最低薪资")
        return self


class JobResponse(JobCreate):
    """岗位接口输出"""

    id: int
    is_active: bool
    factory_name: str | None = None

    model_config = ConfigDict(from_attributes=True)
