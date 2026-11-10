
from dataclasses import dataclass

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage
from langchain_core.tools import tool

from langgraph.graph import (
    StateGraph,
    MessagesState,
    START,
)

from langgraph.prebuilt import (
    ToolNode,
    tools_condition,
    ToolRuntime,
)

from langgraph.runtime import Runtime
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.store.memory import InMemoryStore

from app.config import get_settings

from app.agent.tools.rag_tools import retrieve_policy_tool
from app.agent.tools.apply_tools import apply_job_tools


# 1. 用户运行时上下文
@dataclass
class Context:
    user_id: str


# 2. 保存用户长期求职偏好
@tool
def save_user_preferences(
    preferences: str,
    runtime: ToolRuntime,
) -> str:
    """保存用户明确提出的求职偏好，例如城市、薪资、夜班要求。

    preferences应包含用户当前确认的完整偏好。
    """

    user_id = runtime.context.user_id

    runtime.store.put(
        ("user_preferences",),
        user_id,
        {"preferences": preferences},
    )

    return "用户求职偏好保存成功"


# 3. 读取用户长期偏好
def get_user_preferences(
    runtime: Runtime[Context],
) -> str:

    if runtime.store is None:
        return ""

    user_id = runtime.context.user_id

    item = runtime.store.get(
        ("user_preferences",),
        user_id,
    )

    if not item:
        return ""

    return item.value.get("preferences", "")


# 4. 基础系统提示词
SYSTEM_PROMPT = """
你是BlueHire AI智能招聘助手。

你的主要职责：
1. 根据用户要求查询真实招聘岗位。
2. 回答工厂入职、薪资、住宿等政策问题。
3. 帮助用户申请招聘岗位。
4. 记住用户明确表达的求职偏好。
5. 如果用户陪你闲聊，聊工作以外的，你也要积极配合，像一个传统LLM一样。

工具使用规则：

- 查询岗位必须调用search_jobs。
- 查询工厂政策必须调用retrieve_policy_tool。
- 报名必须调用apply_job_tool。
- 用户明确提出稳定求职偏好时，可调用save_user_preferences。
- 不要编造数据库不存在的岗位及工厂政策。
- 缺少重要报名信息时先向用户确认。
- 不要声称未完成的报名已经成功。
- 回答使用中文，表达清晰自然。

当用户说“第一个岗位”等指代时，
结合当前对话中的岗位查询结果理解。
"""


# 5. Graph构建函数
def build_graph(mcp_tools):

    settings = get_settings()

    # 5.1 初始化DeepSeek
    llm = ChatOpenAI(
        model=settings.deepseek_model,
        api_key=settings.deepseek_api_key,
        base_url=settings.deepseek_base_url,
        temperature=0,
    )

    # 5.2 组合工具
    # search_jobs来自MCP
    # 其余工具来自本地LangChain
    tools = [
        *mcp_tools,
        retrieve_policy_tool,
        apply_job_tools,
        save_user_preferences,
    ]

    tool_names = [item.name for item in tools]

    if len(tool_names) != len(set(tool_names)):
        raise ValueError(
            f"存在重复工具名: {tool_names}"
        )

    if "search_jobs" not in tool_names:
        raise RuntimeError(
            "MCP工具search_jobs未加载"
        )

    # 5.3 DeepSeek绑定工具
    llm_with_tools = llm.bind_tools(tools)

    # 5.4 Agent节点
    async def call_model(
        state: MessagesState,
        runtime: Runtime[Context],
    ):

        preferences = get_user_preferences(runtime)

        system_content = SYSTEM_PROMPT

        if preferences:
            system_content += (
                "\n用户已保存的求职偏好："
                f"{preferences}"
            )

        messages = [
            SystemMessage(content=system_content),
            *state["messages"],
        ]

        # 使用异步模型调用
        response = await llm_with_tools.ainvoke(
            messages
        )

        return {
            "messages": [response]
        }

    # 5.5 构建LangGraph
    workflow = StateGraph(
        MessagesState,
        context_schema=Context,
    )

    # 1. 注册Agent节点
    workflow.add_node(
        "agent",
        call_model,
    )

    # 2. 注册工具节点
    workflow.add_node(
        "tools",
        ToolNode(tools),
    )

    # 3. 指定入口
    workflow.add_edge(
        START,
        "agent",
    )

    # 4. 判断Agent是否需要调用工具
    workflow.add_conditional_edges(
        "agent",
        tools_condition,
    )

    # 5. 工具执行完后回到Agent
    workflow.add_edge(
        "tools",
        "agent",
    )

    # 5.6 内存状态管理
    checkpointer = InMemorySaver()
    store = InMemoryStore()

    # 5.7 编译Graph
    graph = workflow.compile(
        checkpointer=checkpointer,
        store=store,
    )

    print(
        "LangGraph初始化完成，工具列表：",
        tool_names,
        flush=True,
    )

    return graph
