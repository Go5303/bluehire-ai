from fastapi import FastAPI

app = FastAPI(
    title="BlueHire AI",
    description="蓝领智能招聘 Agent 平台",
    version="1.0.0",
)

@app.get("/health", tags=["System"])
async def health() -> dict:
    return {
        "code": 0,
        "message": "success",
        "data": {
            "status": "ok",
            "service": "blueHire-ai-ok",
        }
    }