"""Task 2.1: RAG服务测试"""
import pytest
import os
from pathlib import Path
from services.rag_service import RAGService, RetrievalResult


class TestRAGService:
    """RAG服务测试"""

    def test_rag_service_initialization(self):
        """测试RAG服务初始化"""
        # 使用临时目录
        rag = RAGService(
            docs_path="data/regulations",
            persist_dir="data/test_vector_store",
            collection_name="test_regulations",
        )
        
        assert rag.docs_path == Path("data/regulations")
        assert rag.persist_dir == Path("data/test_vector_store")
        assert rag.collection_name == "test_regulations"
        assert rag.chroma_client is not None
        assert rag.vector_store is not None

    def test_get_statistics_before_build(self):
        """测试构建前的统计信息"""
        rag = RAGService(
            docs_path="data/regulations",
            persist_dir="data/test_vector_store",
            collection_name="test_stats",
        )
        
        stats = rag.get_statistics()
        assert "status" in stats
        assert "total_chunks" in stats
        assert "collection_name" in stats

    def test_retrieval_result_dataclass(self):
        """测试检索结果数据类"""
        result = RetrievalResult(
            relevant_docs=["doc1", "doc2"],
            scores=[0.9, 0.8],
            metadata=[{"source": "file1"}, {"source": "file2"}],
            summary="测试摘要",
        )
        
        assert len(result.relevant_docs) == 2
        assert len(result.scores) == 2
        assert len(result.metadata) == 2
        assert result.summary == "测试摘要"

    def test_generate_summary_empty_docs(self):
        """测试空文档摘要生成"""
        rag = RAGService(
            docs_path="data/regulations",
            persist_dir="data/test_vector_store",
            collection_name="test_summary",
        )
        
        summary = rag._generate_summary([], "测试查询")
        assert "未找到相关法规" in summary

    def test_generate_summary_with_docs(self):
        """测试有文档的摘要生成"""
        rag = RAGService(
            docs_path="data/regulations",
            persist_dir="data/test_vector_store",
            collection_name="test_summary2",
        )
        
        docs = [
            "这是第一条法规内容，包含了一些重要的规定。",
            "这是第二条法规内容，也很重要。",
            "这是第三条法规内容。",
        ]
        
        summary = rag._generate_summary(docs, "测试查询")
        assert "找到 3 条相关法规" in summary
        assert "1." in summary
        assert "2." in summary

    def test_delete_collection(self):
        """测试删除集合"""
        rag = RAGService(
            docs_path="data/regulations",
            persist_dir="data/test_vector_store",
            collection_name="test_delete",
        )
        
        # 删除集合
        result = rag.delete_collection()
        assert result is True
        assert rag.index is None

    def test_settings_configuration(self):
        """测试全局设置配置"""
        from llama_index.core import Settings
        
        rag = RAGService(
            docs_path="data/regulations",
            persist_dir="data/test_vector_store",
            collection_name="test_settings",
            chunk_size=256,
            chunk_overlap=25,
        )
        
        assert Settings.chunk_size == 256
        assert Settings.chunk_overlap == 25
        assert Settings.embed_model is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
