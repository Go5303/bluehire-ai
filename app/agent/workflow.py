import sys

from langchain_core.messages import HumanMessage, SystemMessage

from langgraph.graph import StateGraph, MessagesState, START
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import InMemorySaver

from dataclasses import dataclass

from langgraph.runtime import Runtime

from app.agent.memory import (
    memory_store,
    get_user_preferences,
)

from app.agent.builder import (
    llm_with_tools,
    tools,
    SYSTEM_PROMPT
)


@dataclass
class Context:
    user_id: str

# 1.Agent节点 模型invoke
def call_model(
    state:MessagesState,
    runtime:Runtime[Context],
):
    # 获取当前用户
    user_id = runtime.context.user_id

    # 获取用户长期偏好
    preferences = get_user_preferences(user_id)

    # 把长期偏好放进系统提示词
    system_content = SYSTEM_PROMPT

    if preferences is not None:
        system_content += (
            "\n\n当前用户已保存的求职偏好："
            f"{preferences}"
            "\n当用户没有重新指定条件时，"
            "优先参考这些偏好。"
            "如果用户当前要求与偏好冲突，"
            "以当前明确要求为准。"
        )
    messages = [
        SystemMessage(content=system_content),
        *state["messages"],
    ]

    response = llm_with_tools.invoke(messages)

    return {"messages": [response]}

# 2. 创建工作流
workflow = StateGraph(
    MessagesState,
    context_schema=Context,
)

# 添加模型节点
workflow.add_node("agent", call_model)

# 添加工具节点，自动执行Tool Calling
workflow.add_node("tools", ToolNode(tools))

# 3.配置工作流执行线路
workflow.add_edge(START, "agent")

# 有Tool Call -> tools; 否则 -> END
workflow.add_conditional_edges(
    "agent",
    tools_condition,
)

# 工具执行完成继续执行模型
workflow.add_edge("tools", "agent")

# 4.创建内存 CheckPointer
checkpointer = InMemorySaver()

# 编译图
graph = workflow.compile(
    checkpointer=checkpointer,
    store=memory_store,
)

# 5.对外提供聊天函数
from langgraph.types import Command

def handle_result(result: dict) -> dict:
    """统一处理Graph的正常回答和中断状态"""
    # Graph正在等待用户确认
    if "__interrupt__" in result:
        interrupts = result["__interrupt__"]

        if interrupts:
            return {
                "status": "confirmation_required",
                "data": interrupts[0].value,
            }

        # Graph已正常结束
    return {
        "status": "completed",
        "answer": str(result["messages"][-1].content),
    }

def chat(
        message:str,
        thread_id: str,
        user_id: str
) -> dict:
    config = {
        "configurable": {
            "thread_id": thread_id,
        },
        "recursion_limit": 12,
    }
    input = {
            "messages": [
                HumanMessage(message),
            ]
        }
    result = graph.invoke(
        input=input,
        config=config,
        context=Context(user_id=user_id)
    )

    return handle_result(result)

def confirm_apply(
    approved: bool,
    thread_id: str,
    user_id: str,
) -> dict:
    config = {
        "configurable": {"thread_id": thread_id},
        "recursion_limit": 12,
    }

    # 必须先有等待确认的中断
    state = graph.get_state(config)

    if not state.interrupts:
        return {
            "status": "error",
            "message": "当前会话没有待确认的操作",
        }

    result = graph.invoke(
        Command(resume=approved),
        config=config,
        context=Context(user_id=user_id),
    )

    return handle_result(result)


# 6. 本地测试
if __name__ == "__main__":

    thread_id = "apply_test_001"
    user_id = "user_001"

    # 第一轮：先查询真实岗位
    result1 = chat(
        "帮我找苏州6000以上的工作",
        thread_id,
        user_id
    )
    print("第一轮：\n", result1)

    # 第二轮：申请报名
    result2 = chat(
        "帮我报名刚才推荐的第一个岗位",
        thread_id,
        user_id,
    )
    print("第二轮：\n", result2)

    # 必须出现等待确认，才能继续
    if result2["status"] == "confirmation_required":

        print("等待确认：", result2["data"])
        # 模拟用户点击确认
        result3 = confirm_apply(
            approved=True,
            thread_id=thread_id,
            user_id=user_id,
        )
        print("第三轮：", result3)





