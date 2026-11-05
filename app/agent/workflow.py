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
def chat(message:str,  thread_id: str, user_id: str):
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

    return str(result["messages"][-1].content)

# 6. 本地测试
if __name__ == "__main__":

    from app.agent.memory import save_user_preferences

    thread_id = "test_user_001"

    user_id = "user_001"

    # 第一步：保存长期求职偏好
    save_user_preferences(
        user_id=user_id,
        city="苏州",
        min_salary=6000,
        avoid_night_shift=True,
    )

    # 第二步：第一个会话
    question1 = "你好，我想了解一下你能做什么。"
    answer1 = chat(question1, thread_id, user_id)

    print("\n========== 第一轮 ==========")
    print(answer1)

    # 第三部：新建会话
    question2 = "我之前找工作有什么要求？"
    answer2 = chat(question2, "thread_002", user_id)

    print("\n========== 第二轮 ==========")
    print(answer2)







