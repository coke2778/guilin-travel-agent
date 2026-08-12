# 桂林旅游助手 Agent

基于智谱AI大模型 + Function Calling + RAG 的旅游问答助手。

## 功能

- 实时天气查询
- 美食推荐
- 景点推荐
- 酒店推荐
- 知识库问答（RAG）
- 多轮对话记忆

## 技术栈

- Python 3.13
- 智谱AI API
- SentenceTransformer + FAISS（RAG）
- logging、tenacity（工程化）
- python-dotenv（环境变量）

## 运行方式

1. 安装依赖：`pip install -r requirements.txt`
2. 在 `.env` 中配置 `ZHIPU_API_KEY`
3. 运行：`python zhipu-demo.py`

## 项目截图

（如果你能截一张运行中的对话截图，放上来会更好）

## 目录结构

```
.
├── zhipu-demo.py
├── knowledge.txt
├── tools.py
├── requirements.txt
├── .env
└── .gitignore
```