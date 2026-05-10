# 多智能体协同知识工作台

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104%2B-009688.svg)](https://fastapi.tiangolo.com/)

一个能理解自然语言任务、自动拆解并调度多个智能体协作的系统，支持从本地文档和实时网页中检索知识。

## 一、 核心特性

### 多智能体架构

- **Planner**: LLM 自动拆解任务为子任务列表
- **Coordinator**: 按依赖顺序调度子任务，支持并行执行
- **Specialists**: 多个专家智能体
  - RetrieveSpecialist: 从本地知识库检索
  - CrawlSpecialist: 爬取网页内容
  - AnalyzeSpecialist: 文本分析
  - ExecuteSpecialist: 代码执行
- **Summary**: 汇总所有子任务结果生成最终答案

### 增强型 RAG 流水线

- **混合分块**: 保留代码块、表格、公式的完整性
- **双路检索**: 向量检索（Qdrant）+ BM25 关键词检索
- **RRF 融合**: 倒数排名融合合并检索结果
- **精准重排**: BGE-reranker 重排序

### 爬虫模块

- **静态网页**: requests + BeautifulSoup
- **动态网页**: Selenium 支持
- **反爬策略**: 随机 User-Agent、请求延时
- **断点续爬**: SQLite 记录已爬 URL

### 极简 API

- `POST /task`: 提交任务
- `GET /status/{task_id}`: 查询状态
- `GET /result/{task_id}`: 获取结果

## 二、 技术栈

### 后端

- **框架**: FastAPI
- **LLM**: Ollama（本地模型）
- **向量数据库**: Qdrant
- **嵌入模型**: sentence-transformers/all-MiniLM-L6-v2
- **重排模型**: BAAI/bge-reranker-base
- **BM25**: rank\_bm25
- **爬虫**: requests, BeautifulSoup, Selenium

### 前端

- **纯 HTML/CSS/JavaScript**
- **响应式设计**

## 三、 项目结构

```
multi-agent-workspace/
├── main.py                 # FastAPI 主入口
├── agents/                 # 智能体模块
│   ├── planner/           # 任务规划器
│   ├── coordinator/       # 协调器
│   ├── specialists/       # 专家智能体
│   └── summary/           # 总结器
├── rag/                   # RAG 流水线
│   ├── retriever.py       # 混合检索器
│   └── indexer.py         # 文档索引器
├── crawler/               # 爬虫模块
│   ├── crawler.py         # 网页爬虫
│   └── data_pipeline.py   # 数据管道
├── services/              # 服务模块
│   └── ollama_service.py  # Ollama 服务
├── utils/                 # 工具模块
│   └── logger.py          # 日志工具
├── scripts/               # 脚本
│   └── evaluate.py        # 离线评估
├── web/                   # 前端
│   └── index.html         # Web 界面
├── docs/                  # 文档和截图
│   └── images/            # 项目演示截图
├── data/                  # 数据目录
└── uploads/               # 上传文件
```

## 使用教程

### 环境要求

- Python 3.10+
- Docker（用于 Qdrant）
- Ollama（本地 LLM 服务）

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 启动 Qdrant

```bash
docker run -d --name qdrant -p 6333:6333 qdrant/qdrant
```

### 3. 启动 Ollama

```bash
# 安装 Ollama
# 参考: https://ollama.ai/

# 下载模型
ollama pull deepseek-r1:8b

# 启动服务
ollama serve
```

### 4. 配置环境变量

创建 `.env` 文件：

```bash
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=deepseek-r1:8b
QDRANT_URL=http://localhost:6333
PORT=8000
```

### 5. 启动服务

```bash
python main.py
```

服务启动后，访问：

- API 文档: <http://localhost:8000/docs>
- Web 界面: 打开 `web/index.html`

## 四、 功能展示

### 🎯 主界面展示

系统提供简洁直观的 Web 界面，左侧快速任务导航栏支持一键触发常用功能：

![主界面](docs/images/屏幕截图%202026-05-10%20144257.png)

> 图：多智能体协同工作台主界面，包含4个快速任务入口（文档检索、网页爬取、文本分析、代码生成）

***

### ⚙️ 多智能体协作流程

当用户提交任务后，系统自动拆解并调度多个智能体协作处理，实时展示各智能体的工作状态：

![智能体处理中](docs/images/屏幕截图%202026-05-10%20144322.png)

> 图：智能体实时工作状态 - Planner（规划）、Coordinator（调度）、Specialists（专家执行）、Summary（汇总）

---

## 五、 核心功能演示

### 1️⃣ 文档检索功能（RetrieveSpecialist）

系统能够从本地知识库中检索相关文档，并结合 LLM 提供结构化的知识解答。

**示例查询：** "检索RAG技术相关的知识，包括原理、优势和应用场景"

![RAG检索结果](docs/images/屏幕截图%202026-05-10%20144405.png)

> 图：RAG 技术检索结果 - 展示 RAG 原理（信息检索+生成模型结合）、优势（动态知识更新、精准回答）及应用场景（法律、医疗、金融）

**示例查询：** "检索关于Python项目开发的最佳实践"

![项目开发最佳实践](docs/images/屏幕截图%202026-05-10%20144435.png)

> 图：Python 项目开发规范检索结果 - 包含代码规范（PEP8、Black/pylint）、架构设计（MVC/SOLID原则）及工程化实践（单元测试、Git管理、Linter检查）

---

### 2️⃣ 网页爬取功能（CrawlSpecialist）

支持爬取指定 URL 的网页内容，并自动提取关键信息进行结构化整理。

**示例查询：** "爬取 https://docs.python.org/3/library/asyncio.html 关于异步编程的基本概念"

![网页爬取结果](docs/images/屏幕截图%202026-05-10%20144616.png)

> 图：Python asyncio 文档爬取结果 - 提取关键词（异步编程、事件循环、async/await）并总结核心要点（协程非阻塞I/O、多任务并发执行等）

---

### 3️⃣ 文本分析功能（AnalyzeSpecialist）

对用户提供的文本进行深度分析，包括情感倾向、关键信息提取、趋势分析等。

**示例查询：** "分析以下文本：2024年第一季度，全球智能手机市场出货量达到3.2亿台，同比增长12%。其中5G手机占比超过60%，折叠屏手机增长显著。"

![文本分析结果](docs/images/屏幕截图%202026-05-10%20144752.png)

> 图：市场数据分析报告 - 从市场规模（出货量、5G占比）、趋势分析（5G推动升级、折叠屏渗透）、行业影响（产业链转型、消费敏感度）三个维度进行专业解读

---

### 4️⃣ 代码生成功能（CodeSpecialist）

根据自然语言需求生成高质量、可运行的 Python 代码，包含完整的项目结构和注释说明。

**示例查询：** "用Python FastAPI实现一个待办事项API，包含创建、查询、更新、删除功能"

![代码生成结果](docs/images/屏幕截图%202026-05-10%20144821.png)

> 图：FastAPI 待办事项 API 完整代码生成 - 包含模型定义（Task类）、内存存储、CRUD路由（POST创建/GET查询），代码格式规范且可直接运行

---

### 5️⃣ 综合研究任务（多智能体协作）

对于复杂问题，系统自动拆解子任务并协调多个专家智能体共同完成，最终汇总为完整的研究报告。

**示例查询：** "需要开发一个知识库问答系统，请分析应该选择哪些技术栈"

![技术选型分析](docs/images/屏幕截图%202026-05-10%20145004.png)

> 图：知识库问答系统技术选型方案 - 前端（React/Vue + Ant Design）、后端（Node.js/Django）、数据库（MySQL/MongoDB）、AI模型（TensorFlow/PyTorch）、部署（Docker + K8s）

**示例查询：** "调研2024年最新的大语言模型发展趋势"

![大语言模型研究](docs/images/屏幕截图%202026-05-10%20145053.png)

> 图：2024年LLM发展趋势研究报告 - 从文献综述（LLaMA-3、Qwen2性能指标）、数据收集（NeurIPS/ICML论文）、分析方法（对比评估、多模态潜力）到结论的完整研究框架

---

### 6️⃣ 复杂技术教程生成

能够处理高度专业的技术问题，生成详细的操作步骤和命令行指令。

**示例查询：** "如何Docker容器中部署Python异步Web应用，并配置Nginx反向代理和Let's Encrypt SSL证书"

![Docker部署教程](docs/images/屏幕截图%202026-05-10%20145102.png)

> 图：Docker 部署完整教程 - 分步详解 Dockerfile 创建、Nginx 反向代理配置、certbot SSL 证书申请、证书挂载及测试验证的全流程

---

## 六、 离线评估

运行评估脚本：

```bash
python scripts/evaluate.py
```

评估指标：

- **Recall\@5**: 前5个结果中的召回率
- **Recall\@10**: 前10个结果中的召回率
- **MRR**: 平均倒数排名

## 七、 简历项目描述

**多智能体协同知识工作台（2026.04）**

技术栈：Python, LangChain, Qdrant, rank\_bm25, BGE-reranker, FastAPI, Selenium

- **多智能体架构**：设计 Planner‑Coordinator‑Specialist‑Summary 四层智能体，LLM 自动拆解任务，协调器动态调度检索、爬虫、分析等专家，支持并行执行。
- **增强 RAG 流水线**：混合分块（保留代码/表格）、双路检索（Qdrant 向量 + BM25）、RRF 融合及 BGE 重排序，使复杂文档的 Recall@5 提升 15%+。
- **数据管道**：爬虫模块支持动态网页抓取、断点续爬，数据清洗后自动向量化入库，形成从采集到问答的全链路。
- **后端服务**：基于 FastAPI 提供极简任务接口（/task, /status, /result），便于演示，不强调后端细节。
- **离线评估**：编写评测脚本量化不同检索策略效果，对比向量/混合/重排的召回率。

## 贡献指南

欢迎提交 Issue 和 Pull Request！

## 许可证

本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。
