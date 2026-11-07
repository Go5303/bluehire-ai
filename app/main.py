from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse

from app.api.chat import router as chat_router


app = FastAPI(
    title="BlueHire AI",
    description="蓝领智能招聘 Agent 平台",
    version="0.1.0",
)

# 注册聊天路由
app.include_router(chat_router)

BASE_DIR = Path(__file__).resolve().parent


@app.get("/", include_in_schema=False)
def index():
    return FileResponse(
        BASE_DIR / "static" / "index.html"
    )


@app.get("/health", tags=["System"])
async def health():
    return {
        "code": 0,
        "message": "success",
        "data": {
            "status": "ok",
            "service": "bluehire-ai",
        },
    }