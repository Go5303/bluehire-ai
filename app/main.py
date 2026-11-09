
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse

from app.agent.mcp_client import load_job_mcp_tools
from app.agent.workflow import build_graph
from app.api.chat import router as chat_router


BASE_DIR = Path(__file__).resolve().parent


# FastAPI生命周期
@asynccontextmanager
async def lifespan(app: FastAPI):

    print("正在初始化BlueHire AI...", flush=True)

    # 1. 连接MCP Server并加载工具
    mcp_tools = await load_job_mcp_tools()

    # 2. 构建LangGraph Agent
    graph = build_graph(mcp_tools)

    # 3. 将Graph保存到FastAPI进程
    app.state.graph = graph

    print("BlueHire AI启动成功！", flush=True)

    # FastAPI开始处理HTTP请求
    yield

    print("BlueHire AI服务停止", flush=True)


# 创建FastAPI应用
app = FastAPI(
    title="BlueHire AI",
    description="蓝领智能招聘Agent平台",
    version="1.0.0",
    lifespan=lifespan,
)


# 注册聊天API
app.include_router(chat_router)


# 首页
@app.get("/", include_in_schema=False)
def index():

    return FileResponse(
        BASE_DIR / "static" / "index.html"
    )


# 健康检查
@app.get("/health", tags=["System"])
def health():

    return {
        "code": 0,
        "message": "success",
        "data": {
            "status": "ok",
            "service": "bluehire-ai",
        }
    }
