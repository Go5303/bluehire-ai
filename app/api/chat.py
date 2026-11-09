
import json
import logging

from typing import Any
from collections.abc import AsyncGenerator

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from langchain_core.messages import HumanMessage
from langgraph.types import Command

from app.agent.workflow import Context


router = APIRouter(
    prefix="/api/chat",
    tags=["Chat"],
)

logger = logging.getLogger(__name__)


# 1. 请求Schema
class ChatRequest(BaseModel):
    message: str = Field(min_length=1)
    thread_id: str = Field(min_length=1)
    user_id: str = Field(min_length=1)


class ConfirmRequest(BaseModel):
    thread_id: str = Field(min_length=1)
    user_id: str = Field(min_length=1)
    approved: bool


# 2. SSE事件格式
def sse_event(
    event: str,
    data: dict,
) -> str:

    payload = json.dumps(
        data,
        ensure_ascii=False,
    )

    return (
        f"event: {event}\n"
        f"data: {payload}\n\n"
    )


# 3. LangGraph流式执行
async def stream_graph(
    graph,
    graph_input: Any,
    thread_id: str,
    user_id: str,
) -> AsyncGenerator[str, None]:

    config = {
        "configurable": {
            "thread_id": thread_id,
        },
        "recursion_limit": 20,
    }

    yield sse_event(
        "status",
        {"message": "AI正在思考..."},
    )

    try:

        async for mode, chunk in graph.astream(
            graph_input,
            config=config,
            context=Context(user_id=user_id),
            stream_mode=[
                "messages",
                "updates",
            ],
        ):

            # 3.1 模型Token流式输出
            if mode == "messages":

                message_chunk, metadata = chunk

                # 只发送Agent节点的模型输出
                if metadata.get("langgraph_node") != "agent":
                    continue

                content = message_chunk.content

                if isinstance(content, str) and content:

                    yield sse_event(
                        "token",
                        {"content": content},
                    )

                elif isinstance(content, list):

                    for block in content:

                        if not isinstance(block, dict):
                            continue

                        if (
                            block.get("type") == "text"
                            and isinstance(
                                block.get("text"),
                                str,
                            )
                        ):

                            yield sse_event(
                                "token",
                                {
                                    "content": block["text"]
                                },
                            )

            # 3.2 Graph节点更新
            elif mode == "updates":

                if "agent" in chunk:

                    messages = chunk["agent"].get(
                        "messages",
                        [],
                    )

                    if messages:

                        calls = getattr(
                            messages[-1],
                            "tool_calls",
                            [],
                        )

                        if calls:

                            # 清理工具调用前可能出现的
                            # 临时模型文本
                            yield sse_event(
                                "reset",
                                {},
                            )

                        for call in calls:

                            yield sse_event(
                                "status",
                                {
                                    "message": "正在调用工具",
                                    "tool": call["name"],
                                },
                            )

                if "tools" in chunk:

                    yield sse_event(
                        "status",
                        {
                            "message": (
                                "工具执行完成，正在整理回答"
                            )
                        },
                    )

        # 4. 注意：已退出async for循环
        state = await graph.aget_state(config)

        interrupts = state.interrupts

        if interrupts:

            yield sse_event(
                "confirmation",
                {
                    "data": interrupts[0].value
                },
            )

        # 5. Graph执行结束
        yield sse_event(
            "done",
            {
                "finished": True,
                "interrupted": bool(interrupts),
            },
        )

    except Exception:

        logger.exception(
            "BlueHire SSE执行失败"
        )

        yield sse_event(
            "error",
            {
                "message": (
                    "Agent执行失败，请查看服务端日志"
                )
            },
        )


# 6. 返回SSE Response
def create_stream_response(generator):

    return StreamingResponse(
        generator,
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


# 7. 普通聊天
@router.post("/stream")
async def chat_stream(
    request: ChatRequest,
    http_request: Request,
):

    # 从FastAPI获取Graph
    graph = http_request.app.state.graph

    config = {
        "configurable": {
            "thread_id": request.thread_id,
        }
    }

    state = await graph.aget_state(config)

    # 如果正在等待用户确认报名
    if state.interrupts:

        raise HTTPException(
            status_code=409,
            detail="请先确认或取消当前报名",
        )

    graph_input = {
        "messages": [
            HumanMessage(
                content=request.message,
            )
        ]
    }

    return create_stream_response(
        stream_graph(
            graph,
            graph_input,
            request.thread_id,
            request.user_id,
        )
    )


# 8. 报名确认或取消
@router.post("/confirm")
async def chat_confirm(
    request: ConfirmRequest,
    http_request: Request,
):

    graph = http_request.app.state.graph

    config = {
        "configurable": {
            "thread_id": request.thread_id,
        }
    }

    state = await graph.aget_state(config)

    if not state.interrupts:

        raise HTTPException(
            status_code=409,
            detail="当前会话没有待确认操作",
        )

    return create_stream_response(
        stream_graph(
            graph,
            Command(
                resume=request.approved,
            ),
            request.thread_id,
            request.user_id,
        )
    )
