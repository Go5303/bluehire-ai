from langchain_core.messages import HumanMessage, SystemMessage

from langgraph.graph import StateGraph, MessagesState, START
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import InMemorySaver

from app.agent.builder import (
    llm_with_tools,
    tools,
    SYSTEM_PROMPT
)

# 1.Agent节点 模型invoke
def call_model(state:MessagesState):
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        *state["messages"],
    ]

    response = llm_with_tools.invoke(messages)

    return {"messages": [response]}

# 2. 创建工作流
workflow = StateGraph(MessagesState)

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
graph = workflow.compile(checkpointer=checkpointer)

# 5.对外提供聊天函数
def chat(message:str,  thread_id: str = "user_001"):
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
    result = graph.invoke(input=input, config=config)

    return result["messages"][-1].content

# 6. 本地测试
if __name__ == "__main__":

    thread_id = "test_user_001"

    question1 = "你会想我吗？"
    answer1 = chat(question1, thread_id)

    print("\n========== 第一轮 ==========")
    print(answer1)

    question2 = "但是我总想你怎么办？"
    answer2 = chat(question2, thread_id)

    print("\n========== 第二轮 ==========")
    print(answer2)







