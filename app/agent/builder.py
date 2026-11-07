from langchain_openai import ChatOpenAI
from langchain_core.messages import (
    SystemMessage,
    HumanMessage,
    ToolMessage
)

from app.config import get_settings
from app.agent.tools.job_tools import search_jobs_tool
from app.agent.tools.rag_tools import retrieve_policy_tool
from app.agent.tools.apply_tools import apply_job_tools

# 1、初始化模型（DeepSeek）
modelSetting = get_settings()
llm = ChatOpenAI(
    model=modelSetting.deepseek_model,
    api_key=modelSetting.deepseek_api_key.get_secret_value(),
    base_url=modelSetting.deepseek_base_url,
    temperature=0
)

# 2、注册工具
tools = [
    search_jobs_tool,
    retrieve_policy_tool,
    apply_job_tools,
]

# 模型绑定工具，让ai可以使用自定义的tool
llm_with_tools = llm.bind_tools(
    tools,
    tool_choice="auto",
)

# Python工具注册表
tool_map = {
    tool.name: tool
    for tool in tools
}
SYSTEM_PROMPT = """
你是BlueHire AI蓝领招聘助手。

你拥有三个工具：

1. search_jobs_tool
   用途：查询真实招聘岗位。
   适合城市、工资、夜班、住宿等岗位筛选。

2. retrieve_policy_tool
   用途：检索指定工厂的政策文档。
   适合工资结算、离职、宿舍、体检、入职等问题。
   
3. apply_job_tool
   用途：用户明确要求报名时，申请报名指定岗位。

报名规则：
- 用户必须明确表达报名意愿，才能调用报名工具。
- job_id必须来自已查询到的真实岗位，不可猜测。
- “第一个岗位”等描述，要结合历史消息确定岗位ID。
- 无法确定具体岗位时，先向用户询问。
- 报名工具会暂停并等待用户确认。
- 未收到工具成功结果前，不能声称报名成功。

规则：
- 根据用户问题自主选择工具。
- 如果同时需要多个工具，可以连续调用。
- 不需要工具的问题，可以直接回答。
- 查询岗位必须依据MySQL返回的真实数据。
- 回答工厂政策必须依据Chroma返回的原文。
- 查询政策前必须明确factory_id，不允许编造。
- 检索结果没有相关依据时，应说明资料不足。
- 不要编造岗位、工资政策或报名结果。
"""

# 3、同一个agent多工具执行
def run_job_agent(user_input:str = None) -> str:

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=user_input),
    ]

    # 最多允许5轮模型工具调用
    max_rounds = 5

    for round_number in range(max_rounds):

        print(f"\n========== 第{round_number+1}轮 ==========")

        # 模型决定：调用工具还是直接回答
        ai_message = llm_with_tools.invoke(messages)

        messages.append(ai_message)

        # 模型invoke之后，发现不需要调用工具，说明模型已经给出回答
        if not ai_message.tool_calls:
            return str(ai_message.content)

        # 模型可能一次调用多个工具
        for tool_call in ai_message.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]

            print(f"工具名称：{tool_name},工具参数：{tool_args}")

            tool_obj = tool_map.get(tool_name)

            if tool_obj is None:
                result = f"错误：不存在工具 {tool_name}"
            else:
                try:
                    result = tool_obj.invoke(tool_args)
                except Exception as exc:
                    print("工具执行异常：", exc)
                    result = "工具执行失败，请告知用户稍后重试"

            print("工具返回结果：", result)

            messages.append(
                ToolMessage(
                    content=str(result),
                    tool_call_id=tool_call["id"],
                ),
            )
    # 防止Agent无限循环
    # 达到上限后不再允许模型调用工具
    print("已达到最大工具调用轮数")

    messages.append(
        HumanMessage(
            content="请根据已有工具结果给出最终回答，不要再调用工具。"
        )
    )

    final_message = llm.invoke(messages)

    return str(final_message.content)





