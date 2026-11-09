from mcp.server.fastmcp import FastMCP

from app.agent.tools.job_tools import search_jobs_tool


# 1. 创建MCP Server
mcp = FastMCP("BlueHire Jobs")


# 2. 注册MCP工具
@mcp.tool()
def search_jobs(
    city: str | None = None,
    min_salary: int | None = None,
    has_night_shift: bool | None = None,
    provide_accommodation: bool | None = None,
    limit: int = 10,
) -> str:
    """
    查询BlueHire招聘岗位。

    支持城市、最低月薪、是否夜班、
    是否提供住宿及返回数量等条件。

    数据来自MySQL。
    """

    params = {
        "city": city,
        "min_salary": min_salary,
        "has_night_shift": has_night_shift,
        "provide_accommodation": provide_accommodation,
        "limit": limit,
    }

    # 只传实际提供的筛选条件
    params = {
        key: value
        for key, value in params.items()
        if value is not None
    }

    # 校验MCP参数与原有LangChain Tool是否一致
    schema = search_jobs_tool.args_schema

    allowed = set(schema.model_fields)

    unsupported = set(params) - allowed

    if unsupported:
        raise ValueError(
            f"原岗位工具不支持这些参数: {sorted(unsupported)}"
        )

    # 3. 复用原来的MySQL岗位查询逻辑
    result = search_jobs_tool.invoke(params)

    # 4. 将结果返回给MCP Client
    return str(result)


# 5. 启动stdio MCP Server
if __name__ == "__main__":
    mcp.run(transport="stdio")
