from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage
from langchain_openai import ChatOpenAI

from app.agent.tools.job_tools import search_jobs_tool
from app.config import get_settings

# 1、初始化模型（DeepSeek）
modelSetting = get_settings()
llm = ChatOpenAI(
    model=modelSetting.deepseek_model,
    api_key=modelSetting.deepseek_api_key.get_secret_value(),
    base_url=modelSetting.deepseek_base_url,
)

# 2、注册工具
tools = [search_jobs_tool]

# 模型绑定工具，让ai可以使用自定义的tool
llm_with_tools = llm.bind_tools(tools)

# Python工具注册表
tool_map = {
    tool.name: tool
    for tool in tools
}

# 3、开始创建agent,并开始对话
def run_job_agent(user_input:str = None) -> str:
    messages = [
        SystemMessage(content="""
                    你是BlueHire AI蓝领招聘助手。
                    你的任务：
                    1. 理解求职者的自然语言需求。
                    2. 需要查询岗位时调用search_jobs_tool。
                    3. 从用户输入中提取城市、薪资、夜班和住宿要求。
                    4. 不要编造数据库里不存在的岗位。
                    5. 如果查询不到岗位，要如实告知用户。
                    6. 推荐岗位时尽量展示工厂、岗位、薪资和班次。
                    注意：
                    目前min_salary表示用户期望的最低薪资。
                    如果用户提出的条件超出工具支持范围，
                    请说明当前无法精确筛选的条件。
           """),
        HumanMessage(content=user_input),
    ]
    # 4、开始对话
    ai_message = llm_with_tools.invoke(messages)

    # 把模型响应加入上下文
    messages.append(ai_message)

    # 5、执行模型请求调用的工具
    for tool_call in ai_message.tool_calls:
        tool_name = tool_call["name"]
        tool_args = tool_call["args"]

        print(f"\n工具名称: {tool_name}")
        print(f"工具参数: {tool_args}")

        tool_obj = tool_map.get(tool_name)
        try:
            result = tool_obj.invoke(tool_args)
        except Exception as exc:
            print(f"工具执行失败: {exc}")
            result = "工具执行失败，请稍后重试"
        print(f"工具结果: {result}")

        # 将结果作为ToolMessage反馈给模型
        messages.append(
            ToolMessage(
                content=result,
                tool_call_id=tool_call["id"],
            )
        )

    # 6、第二次调用模型，把系统提示词、用户提示词、工具响应一起给到大模型
    final_message = llm.invoke(messages)

    return final_message.content

if __name__ == "__main__":
    humanQuestion = "帮我找苏州月薪6000以上，长白班，包吃住的工作"

    answer = run_job_agent(user_input=humanQuestion)

    print("-------------------")
    print(answer)
    print("--------------------")









