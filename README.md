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
├── data/                  # 数据目录
└── uploads/               # 上传文件
```

##  使用教程

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

### 🖥️ 界面概览

![主界面首页](docs/images/屏幕截图%202026-05-10%20144257.png)

> 图：Web 界面主页面，左侧提供快速任务入口（文档检索、网页爬取、文本分析、代码生成），右侧为智能对话区域

---

### ⚡ 多智能体实时协作

当用户提交任务后，系统自动拆解并调度多个智能体协同工作：

![多智能体处理进度](docs/images/屏幕截图%202026-05-10%20144322.png)

> 图：实时展示 Planner（规划）、Coordinator（协调）、Specialists（专家）、Summary（汇总）四个阶段的工作状态和进度条

---

### 🔍 文档检索功能 (RAG)

支持从本地知识库中精准检索相关文档：

**示例：RAG 技术知识检索**

![RAG检索结果](docs/images/屏幕截图%202026-05-10%20144405.png)

> 图：检索 RAG（检索增强生成）技术相关文档，返回包含原理、优势和应用场景的结构化知识

**示例：Python 项目开发规范**

![Python开发实践检索](docs/images/屏幕截图%202026-05-10%20144435.png)

> 图：检索 Python 项目开发最佳实践，涵盖 PEP8 规范、MVC 架构设计、DRY/WET 原则等工程实践

---

### 🌐 网页爬取功能

自动识别 URL 并爬取网页内容进行分析：

![网页爬取结果](docs/images/屏幕截图%202026-05-10%20144616.png)

> 图：爬取 Python 官方文档关于 asyncio 的内容，提取关键词（异步编程、事件循环、async/await）并总结核心要点

---

### 📊 文本分析功能

对输入文本进行深度分析和洞察提取：

![市场数据分析](docs/images/屏幕截图%202026-05-10%20144752.png)

> 图：分析智能手机市场数据，输出市场规模、趋势分析（5G普及推动市场升级）、行业影响等多维度结论

---

### 💻 代码生成功能

根据自然语言需求生成高质量可运行的代码：

![FastAPI代码生成](docs/images/屏幕截图%202026-05-10%20144821.png)

> 图：根据"用 FastAPI 实现待办事项 API"的需求，自动生成完整的模型定义、路由创建、内存存储等代码

---

### 🎯 技术选型分析

针对复杂问题提供全面的技术方案建议：

![技术栈选择](docs/images/屏幕截图%202026-05-10%20145004.png)

> 图：分析知识库问答系统的技术选型，覆盖前端（React/Vue）、后端（Node.js/Django）、数据库、AI模型、部署等全栈建议

---

### 🔬 综合研究任务

支持端到端的深度研究工作流：

![大模型趋势研究](docs/images/屏幕截图%202026-05-10%20145053.png)

> 图：完成"2024年大语言模型发展趋势研究"综合任务，输出文献综述、数据收集、分析方法、结论等完整研究报告

---

### 🛠️ 复杂技术教程

能够处理高难度的专业技术查询：

![Docker部署教程](docs/images/屏幕截图%202026-05-10%20145102.png)

> 图：解答 Docker 容器部署 Python 异步 Web 应用的完整教程，包含 Nginx 反向代理配置、Let's Encrypt SSL 证书申请等详细步骤

---

## 五、 离线评估

运行评估脚本：

```bash
python scripts/evaluate.py
```

评估指标：

- **Recall\@5**: 前5个结果中的召回率
- **Recall\@10**: 前10个结果中的召回率
- **MRR**: 平均倒数排名

##  贡献指南

欢迎提交 Issue 和 Pull Request！

##  许可证

本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。
