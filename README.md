# BlueHire AI — 蓝领智能招聘 Agent

基于 **DeepSeek + LangChain + LangGraph** 构建的蓝领智能招聘 Agent，融合 MCP、RAG、Tool Calling、多轮会话记忆及 SSE 流式交互，实现自然语言岗位匹配、工厂政策问答与智能报名等核心业务功能。

本项目面向 AI Agent 应用开发实践，重点展示大模型与真实业务数据库、向量知识库及可控业务工作流的集成能力。

## 一、技术栈

| 模块 | 技术 |
|---|---|
| 开发语言 | Python 3.11 |
| Web框架 | FastAPI、Pydantic |
| 大语言模型 | DeepSeek |
| Agent框架 | LangChain、LangGraph |
| 工具协议 | MCP、LangChain MCP Adapter |
| Embedding | 阿里百炼 text-embedding-v4 |
| 向量数据库 | Chroma |
| 业务数据库 | MySQL、SQLAlchemy |
| 状态与记忆 | InMemorySaver、InMemoryStore |
| 流式通信 | SSE、LangGraph astream |
| 开发环境 | macOS、Docker、Git |

## 二、核心功能

### 1. 智能岗位检索

用户通过自然语言表达求职需求，Agent自动识别城市、期望薪资、夜班及住宿条件，并通过MCP岗位查询工具访问MySQL，返回符合筛选条件的招聘岗位。

示例：

> 帮我找苏州6000元以上、不上夜班的工作。

### 2. RAG工厂政策问答

基于阿里百炼Embedding与Chroma构建工厂政策知识库，支持对薪资结算、住宿、入职等政策进行语义检索。

结合工厂ID元数据过滤，减少不同工厂政策之间的混用。

示例：

> 1001工厂的工资结算政策是什么？

### 3. LangGraph多工具Agent

通过StateGraph、ToolNode及条件路由管理Agent执行流程，支持动态选择岗位查询、政策检索和报名工具，实现多轮工具调用。

其中岗位查询通过MCP Adapter连接独立MCP Server，复用现有业务数据库查询逻辑。

### 4. 多轮会话与长期偏好记忆

使用LangGraph Checkpointer维护单个thread_id的会话状态，使用Store维护user_id维度的跨会话求职偏好。

支持多轮上下文关联以及不同会话之间的求职偏好共享。

### 5. Agent智能报名

通过LangGraph interrupt与Command恢复机制，实现报名操作前的人工确认。

用户确认后执行MySQL写入，并通过数据库唯一约束保护重复报名场景；取消报名则不执行写入。

### 6. SSE实时聊天

基于FastAPI StreamingResponse和LangGraph astream实现实时流式回答。

Web界面支持工具执行状态展示、报名确认及取消，提供完整的Agent交互体验。

## 三、系统架构

```text
Browser / Web Chat
        |
        | HTTP + SSE
        v
FastAPI
        |
        v
LangGraph Agent
        |
        +---- DeepSeek LLM
        |
        +---- MCP Adapter
        |          |
        |          v
        |      MCP Server
        |          |
        |          v
        |        MySQL
        |
        +---- RAG Tool
        |          |
        |          v
        |     Embedding + Chroma
        |
        +---- Apply Tool
        |          |
        |          v
        |    interrupt + MySQL
        |
        +---- Checkpointer / Store
                   |
                   v
              In-Memory
```

## 四、项目目录

```text
bluehire-ai/
├── app/
│   ├── agent/
│   │   ├── workflow.py
│   │   ├── mcp_client.py
│   │   └── tools/
│   │       ├── job_tools.py
│   │       ├── rag_tools.py
│   │       └── apply_tools.py
│   ├── api/
│   │   └── chat.py
│   ├── db/
│   │   ├── database.py
│   │   ├── models.py
│   │   └── repository.py
│   ├── mcp/
│   │   └── server.py
│   ├── rag/
│   │   ├── embeddings.py
│   │   └── vector_store.py
│   ├── schemas/
│   ├── static/
│   │   └── index.html
│   ├── config.py
│   └── main.py
├── data/
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

## 五、本地启动

### 环境要求

- Python 3.11
- MySQL 8.0
- DeepSeek API Key
- 阿里百炼 API Key

### 1. 克隆项目

```bash
git clone https://github.com/Go5303/bluehire-ai.git
cd bluehire-ai
```

### 2. 创建Python虚拟环境

```bash
python3.11 -m venv .venv
source .venv/bin/activate
```

### 3. 安装依赖

```bash
python -m pip install -r requirements.txt
```

### 4. 配置环境变量

```bash
cp .env.example .env
```

按`.env.example`中的字段配置DeepSeek、阿里百炼及MySQL连接信息。

### 5. 初始化数据

启动MySQL并准备岗位、工厂及报名业务表和演示数据。

根据项目的向量知识库初始化逻辑，导入工厂政策文本，生成Embedding并写入Chroma。

**注意：** 本地Chroma索引不纳入Git版本管理，新环境必须先初始化知识库才能进行RAG问答。

### 6. 启动服务

在项目根目录执行：

```bash
fastapi dev
```

或者：

```bash
python -m uvicorn app.main:app --port 8000
```

访问：

http://127.0.0.1:8000

健康检查：

http://127.0.0.1:8000/health

## 六、功能测试示例

- 岗位检索：帮我找苏州6000元以上的工作。
- 组合条件：不要夜班，最好提供住宿。
- 政策问答：1001工厂的工资结算政策是什么？
- 多轮上下文：刚才第一个岗位怎么样？
- 长期偏好：记住我只考虑苏州的工作。
- 智能报名：帮我报名第一个岗位。
- 人工确认：选择确认或取消报名。

## 七、Dev版本说明

本项目目前为开发与技术演示版本：

- Checkpointer采用InMemorySaver。
- Store采用InMemoryStore。
- 服务重启后内存会话状态及求职偏好将丢失。
- MCP通过本地stdio通信。
- 默认单Worker运行。
- 不包含生产环境身份认证及分布式状态持久化。
- MySQL业务数据和Chroma向量数据独立于进程内存。

## 八、后续扩展方向

- Checkpointer和Store持久化
- RAG检索效果评测与优化
- Agent工具异常恢复和可观测性
- 用户认证及会话隔离
- 多Worker和容器化部署

## 项目地址

https://github.com/Go5303/bluehire-ai
