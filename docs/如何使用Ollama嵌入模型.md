# 如何使用Ollama BGE-M3嵌入模型

## 🚀 快速开始（5分钟）

### 1. 安装Ollama

**macOS:**
```bash
brew install ollama
```

**Linux:**
```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

**Windows:**
下载安装包: https://ollama.ai/download

### 2. 启动Ollama服务

```bash
ollama serve
```

### 3. 下载BGE-M3模型

```bash
ollama pull bge-m3
```

### 4. 配置环境变量

创建或编辑 `.env` 文件：
```env
# RAG嵌入模型配置
EMBEDDING_MODEL_TYPE=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_EMBEDDING_MODEL=bge-m3
```

### 5. 重建RAG索引

```bash
cd /Users/zelaszang/Documents/UGit/content-moderation-system

# 删除旧索引
rm -rf data/vector_store

# 重建索引
pipenv run python scripts/build_rag_index.py
```

### 6. 运行测试

```bash
# 测试Ollama连接
pipenv run python -m pytest tests/test_ollama_embedding.py -v -s

# 测试RAG集成
pipenv run python -m pytest tests/test_task_2_4.py -v -s
```

---

## 🔄 切换嵌入模型

### 使用Ollama（推荐）

```bash
export EMBEDDING_MODEL_TYPE=ollama
export OLLAMA_BASE_URL=http://localhost:11434
export OLLAMA_EMBEDDING_MODEL=bge-m3
```

### 使用OpenAI

```bash
export EMBEDDING_MODEL_TYPE=openai
export OPENAI_API_KEY=your_api_key
```

**注意**: 切换模型后需要重建索引！

---

## ✅ 验证安装

### 检查Ollama服务
```bash
curl http://localhost:11434/api/tags
```

### 检查BGE-M3模型
```bash
ollama list | grep bge-m3
```

### 运行快速测试
```bash
pipenv run python -c "
from llama_index.embeddings.ollama import OllamaEmbedding
embed = OllamaEmbedding(model_name='bge-m3', base_url='http://localhost:11434')
result = embed.get_text_embedding('测试文本')
print(f'✅ 嵌入生成成功，向量维度: {len(result)}')
"
```

---

## 📊 性能对比

| 指标 | OpenAI | Ollama BGE-M3 |
|-----|--------|---------------|
| 成本 | $0.02/1M tokens | 免费 |
| 延迟 | ~200ms | ~50ms |
| 数据安全 | 云端 | 本地 |
| 向量维度 | 1536 | 1024 |

---

## ❓ 常见问题

### Q1: Ollama服务无法启动？
```bash
# 检查端口占用
lsof -i :11434

# 重启服务
pkill ollama
ollama serve
```

### Q2: 模型下载失败？
```bash
# 使用代理
export https_proxy=http://127.0.0.1:7890
ollama pull bge-m3
```

### Q3: 嵌入生成很慢？
- 检查CPU使用率
- 考虑使用GPU加速
- 使用批量嵌入

### Q4: 如何回退到OpenAI？
```bash
# 修改.env
EMBEDDING_MODEL_TYPE=openai
OPENAI_API_KEY=your_key

# 重建索引
rm -rf data/vector_store
pipenv run python scripts/build_rag_index.py
```

---

## 📚 更多信息

- [Ollama官方文档](https://ollama.ai/docs)
- [BGE-M3模型介绍](https://github.com/FlagOpen/FlagEmbedding)
- [LlamaIndex Ollama集成](https://docs.llamaindex.ai/en/stable/examples/embeddings/ollama_embedding/)
- [完整测试报告](./Ollama集成测试报告.md)

---

## 💡 提示

- ✅ 首次使用需要下载模型（~1.2GB）
- ✅ 确保Ollama服务在后台运行
- ✅ 切换模型后必须重建索引
- ✅ 建议在生产环境使用Ollama降低成本
