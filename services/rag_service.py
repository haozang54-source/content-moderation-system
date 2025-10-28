"""RAG检索服务 - 基于LlamaIndex"""
import os
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass

from llama_index.core import (
    VectorStoreIndex,
    SimpleDirectoryReader,
    StorageContext,
    load_index_from_storage,
    Settings,
)
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.embeddings.ollama import OllamaEmbedding
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.core.node_parser import SentenceSplitter
import chromadb


@dataclass
class RetrievalResult:
    """检索结果"""
    relevant_docs: List[str]
    scores: List[float]
    metadata: List[Dict]
    summary: str


class RAGService:
    """RAG检索服务"""

    def __init__(
        self,
        docs_path: str = "data/regulations",
        persist_dir: str = "data/vector_store",
        collection_name: str = "regulations",
        embedding_model: str = "text-embedding-3-small",
        chunk_size: int = 512,
        chunk_overlap: int = 50,
    ):
        """初始化RAG服务
        
        Args:
            docs_path: 法规文档目录
            persist_dir: 向量存储持久化目录
            collection_name: 集合名称
            embedding_model: 嵌入模型
            chunk_size: 文本块大小
            chunk_overlap: 文本块重叠大小
        """
        self.docs_path = Path(docs_path)
        self.persist_dir = Path(persist_dir)
        self.collection_name = collection_name
        
        # 配置全局设置 - 根据配置选择嵌入模型
        embedding_type = os.getenv("EMBEDDING_MODEL_TYPE", "ollama")
        
        if embedding_type == "ollama":
            # 使用Ollama本地模型
            ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
            ollama_model = os.getenv("OLLAMA_EMBEDDING_MODEL", "bge-m3")
            Settings.embed_model = OllamaEmbedding(
                model_name=ollama_model,
                base_url=ollama_base_url,
            )
            print(f"✅ 使用Ollama嵌入模型: {ollama_model} @ {ollama_base_url}")
        else:
            # 使用OpenAI
            Settings.embed_model = OpenAIEmbedding(
                model=embedding_model,
                api_key=os.getenv("OPENAI_API_KEY"),
            )
            print(f"✅ 使用OpenAI嵌入模型: {embedding_model}")
        
        Settings.chunk_size = chunk_size
        Settings.chunk_overlap = chunk_overlap
        
        # 初始化向量存储
        self.chroma_client = chromadb.PersistentClient(path=str(self.persist_dir))
        self.chroma_collection = self.chroma_client.get_or_create_collection(
            name=self.collection_name
        )
        self.vector_store = ChromaVectorStore(chroma_collection=self.chroma_collection)
        
        # 初始化或加载索引
        self.index: Optional[VectorStoreIndex] = None
        self._initialize_index()

    def _initialize_index(self) -> None:
        """初始化或加载索引"""
        storage_context = StorageContext.from_defaults(vector_store=self.vector_store)
        
        # 检查是否已有索引
        if self.chroma_collection.count() > 0:
            print(f"加载已有索引，文档数: {self.chroma_collection.count()}")
            self.index = VectorStoreIndex.from_vector_store(
                self.vector_store,
                storage_context=storage_context,
            )
        else:
            print("未找到已有索引，需要构建新索引")
            self.index = None

    def build_index(self, force_rebuild: bool = False) -> Dict:
        """构建向量索引
        
        Args:
            force_rebuild: 是否强制重建索引
            
        Returns:
            Dict: 构建统计信息
        """
        if not self.docs_path.exists():
            raise FileNotFoundError(f"文档目录不存在: {self.docs_path}")

        # 如果强制重建，清空现有集合
        if force_rebuild and self.chroma_collection.count() > 0:
            print("清空现有索引...")
            self.chroma_client.delete_collection(name=self.collection_name)
            self.chroma_collection = self.chroma_client.create_collection(
                name=self.collection_name
            )
            self.vector_store = ChromaVectorStore(chroma_collection=self.chroma_collection)

        # 加载文档
        print(f"从 {self.docs_path} 加载文档...")
        documents = SimpleDirectoryReader(
            input_dir=str(self.docs_path),
            recursive=True,
            required_exts=[".txt", ".md", ".pdf", ".docx"],
        ).load_data()

        if not documents:
            raise ValueError(f"未找到任何文档: {self.docs_path}")

        print(f"加载了 {len(documents)} 个文档")

        # 创建索引
        storage_context = StorageContext.from_defaults(vector_store=self.vector_store)
        
        # 使用句子分割器
        text_splitter = SentenceSplitter(
            chunk_size=Settings.chunk_size,
            chunk_overlap=Settings.chunk_overlap,
        )
        
        self.index = VectorStoreIndex.from_documents(
            documents,
            storage_context=storage_context,
            transformations=[text_splitter],
            show_progress=True,
        )

        stats = {
            "total_documents": len(documents),
            "total_chunks": self.chroma_collection.count(),
            "collection_name": self.collection_name,
            "persist_dir": str(self.persist_dir),
        }

        print(f"索引构建完成: {stats}")
        return stats

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        similarity_threshold: float = 0.7,
    ) -> RetrievalResult:
        """检索相关文档
        
        Args:
            query: 查询文本
            top_k: 返回top-k个结果
            similarity_threshold: 相似度阈值
            
        Returns:
            RetrievalResult: 检索结果
        """
        if not self.index:
            raise ValueError("索引未初始化，请先调用 build_index()")

        # 创建查询引擎
        query_engine = self.index.as_query_engine(
            similarity_top_k=top_k,
            response_mode="no_text",  # 只返回节点，不生成回答
        )

        # 执行检索
        response = query_engine.query(query)

        # 提取结果
        relevant_docs = []
        scores = []
        metadata = []

        for node in response.source_nodes:
            # 检查相似度阈值
            if node.score >= similarity_threshold:
                relevant_docs.append(node.node.get_content())
                scores.append(node.score)
                metadata.append(node.node.metadata)

        # 生成摘要
        summary = self._generate_summary(relevant_docs, query)

        return RetrievalResult(
            relevant_docs=relevant_docs,
            scores=scores,
            metadata=metadata,
            summary=summary,
        )

    def _generate_summary(self, docs: List[str], query: str) -> str:
        """生成检索结果摘要
        
        Args:
            docs: 检索到的文档列表
            query: 查询文本
            
        Returns:
            str: 摘要
        """
        if not docs:
            return "未找到相关法规"

        # 简单摘要：返回最相关的前3个文档片段
        top_docs = docs[:3]
        summary = f"找到 {len(docs)} 条相关法规，最相关的内容包括：\n"
        for i, doc in enumerate(top_docs, 1):
            # 截取前200字符
            snippet = doc[:200] + "..." if len(doc) > 200 else doc
            summary += f"\n{i}. {snippet}\n"

        return summary

    def add_documents(self, file_paths: List[str]) -> Dict:
        """添加新文档到索引
        
        Args:
            file_paths: 文档路径列表
            
        Returns:
            Dict: 添加统计信息
        """
        if not self.index:
            raise ValueError("索引未初始化，请先调用 build_index()")

        # 加载新文档
        documents = []
        for file_path in file_paths:
            docs = SimpleDirectoryReader(input_files=[file_path]).load_data()
            documents.extend(docs)

        if not documents:
            return {"added_documents": 0, "added_chunks": 0}

        # 添加到索引
        for doc in documents:
            self.index.insert(doc)

        stats = {
            "added_documents": len(documents),
            "added_chunks": self.chroma_collection.count(),
        }

        print(f"添加文档完成: {stats}")
        return stats

    def delete_collection(self) -> bool:
        """删除集合
        
        Returns:
            bool: 是否删除成功
        """
        try:
            self.chroma_client.delete_collection(name=self.collection_name)
            self.index = None
            print(f"集合 {self.collection_name} 已删除")
            return True
        except Exception as e:
            print(f"删除集合失败: {e}")
            return False

    def get_statistics(self) -> Dict:
        """获取统计信息
        
        Returns:
            Dict: 统计信息
        """
        if not self.index:
            return {
                "status": "未初始化",
                "total_chunks": 0,
                "collection_name": self.collection_name,
            }

        return {
            "status": "已初始化",
            "total_chunks": self.chroma_collection.count(),
            "collection_name": self.collection_name,
            "persist_dir": str(self.persist_dir),
            "embedding_model": Settings.embed_model.model_name,
            "chunk_size": Settings.chunk_size,
            "chunk_overlap": Settings.chunk_overlap,
        }
