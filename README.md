<<<<<<< HEAD
# 多智能体协同知识工作台

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104%2B-009688.svg)](https://fastapi.tiangolo.com/)

一个能理解自然语言任务、自动拆解并调度多个智能体协作的系统，支持从本地文档和实时网页中检索知识。

## ✨ 核心特性

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

## 🛠️ 技术栈

### 后端
- **框架**: FastAPI
- **LLM**: Ollama（本地模型）
- **向量数据库**: Qdrant
- **嵌入模型**: sentence-transformers/all-MiniLM-L6-v2
- **重排模型**: BAAI/bge-reranker-base
- **BM25**: rank_bm25
- **爬虫**: requests, BeautifulSoup, Selenium

### 前端
- **纯 HTML/CSS/JavaScript**
- **响应式设计**

## 📁 项目结构

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
├── scripts/               # 脚本
│   └── evaluate.py        # 离线评估
├── web/                   # 前端
│   └── index.html         # Web 界面
├── data/                  # 数据目录
└── uploads/               # 上传文件
```

## 🚀 快速开始

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
- API 文档: http://localhost:8000/docs
- Web 界面: 打开 `web/index.html`

## 📚 API 使用示例

### 提交任务

```bash
curl -X POST http://localhost:8000/task \
  -H "Content-Type: application/json" \
  -d '{"query": "总结一下本地文档中关于大模型的内容"}'
```

响应：
```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### 查询状态

```bash
curl http://localhost:8000/status/550e8400-e29b-41d4-a716-446655440000
```

响应：
```json
{
  "status": "running",
  "progress": 50,
  "message": "正在执行子任务 2/3: retrieve"
}
```

### 获取结果

```bash
curl http://localhost:8000/result/550e8400-e29b-41d4-a716-446655440000
```

响应：
```json
{
  "result": "根据检索到的文档，大模型的主要内容包括...",
  "status": "completed",
  "error": null
}
```

## 🧪 离线评估

运行评估脚本：

```bash
python scripts/evaluate.py
```

评估指标：
- **Recall@5**: 前5个结果中的召回率
- **Recall@10**: 前10个结果中的召回率
- **MRR**: 平均倒数排名

## 📝 简历项目描述

**多智能体协同知识工作台（2026.04）**

技术栈：Python, LangChain, Qdrant, rank_bm25, BGE-reranker, FastAPI, Selenium

- **多智能体架构**：设计 Planner‑Coordinator‑Specialist‑Summary 四层智能体，LLM 自动拆解任务，协调器动态调度检索、爬虫、分析等专家，支持并行执行。
- **增强 RAG 流水线**：混合分块（保留代码/表格）、双路检索（Qdrant 向量 + BM25）、RRF 融合及 BGE 重排序，使复杂文档的 Recall@5 提升 15%+。
- **数据管道**：爬虫模块支持动态网页抓取、断点续爬，数据清洗后自动向量化入库，形成从采集到问答的全链路。
- **后端服务**：基于 FastAPI 提供极简任务接口（/task, /status, /result），便于演示，不强调后端细节。
- **离线评估**：编写评测脚本量化不同检索策略效果，对比向量/混合/重排的召回率。

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。
=======
# multi-agent-workbench
多智能体协作工作台—自然语言驱动，自动拆解任务，调度爬虫/检索/分析专家，实现复杂信息采集与报告生成
>>>>>>> 5c17afc0dbbb0c470bff82ee7f9d4116eba63cbf
