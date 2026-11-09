import os
import sys
from pathlib import Path

from langchain_mcp_adapters.client import MultiServerMCPClient

BASE_DIR = Path(__file__).resolve().parents[2]

def create_mcp_client() -> MultiServerMCPClient:
    """
    创建MCP客户端。
    使用当前Python解释器启动独立MCP Server进程。
    """
    return MultiServerMCPClient(
        {
            "bluehire_jobs": {
                "transport": "stdio",
                "command": sys.executable,
                "args": [
                    "-m",
                    "app.mcp.server",
                ],
                "cwd": str(BASE_DIR),
                "env": os.environ.copy(),
            }
        }
    )

async def load_job_mcp_tools():
    """
    将MCP工具转换为LangChain工具。
    """
    client = create_mcp_client()

    tools = await client.get_tools()

    print(
        "MCP工具加载成功：",
        [tool.name for tool in tools],
        flush=True,
    )

    if not any(
        tool.name == "search_jobs"
        for tool in tools
    ):
        raise RuntimeError(
            "未找到MCP岗位查询工具search_jobs"
        )

    return tools


























