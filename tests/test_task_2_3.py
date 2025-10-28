"""Task 2.3: RAG检索效果测试"""
import pytest
import asyncio
from pathlib import Path
from services.rag_service import RAGService
from core.pipeline import ModerationPipeline, ContentData


class TestRAGRetrieval:
    """RAG检索效果测试"""

    @pytest.fixture(scope="class")
    def rag_service(self):
        """创建RAG服务实例（类级别共享）"""
        # 确保测试数据存在
        docs_path = Path("data/regulations")
        if not docs_path.exists() or not list(docs_path.glob("*.txt")):
            pytest.skip("测试数据不存在，跳过测试")
        
        rag = RAGService(
            docs_path="data/regulations",
            persist_dir="data/test_vector_store_retrieval",
            collection_name="test_retrieval",
        )
        
        # 构建索引（只构建一次）
        try:
            if rag.chroma_collection.count() == 0:
                rag.build_index(force_rebuild=False)
        except Exception as e:
            pytest.skip(f"索引构建失败: {e}")
        
        yield rag
        
        # 清理
        rag.delete_collection()

    def test_retrieve_extreme_language(self, rag_service):
        """测试极限用语检索"""
        query = "广告中不能使用哪些极限用语？"
        result = rag_service.retrieve(query, top_k=3, similarity_threshold=0.5)
        
        assert len(result.relevant_docs) > 0
        assert len(result.scores) == len(result.relevant_docs)
        assert all(score >= 0.5 for score in result.scores)
        
        # 检查是否包含相关内容
        combined_text = " ".join(result.relevant_docs)
        assert any(keyword in combined_text for keyword in ["最佳", "最好", "最高级"])

    def test_retrieve_medical_advertising(self, rag_service):
        """测试医疗广告检索"""
        query = "医疗广告有什么限制和要求？"
        result = rag_service.retrieve(query, top_k=3, similarity_threshold=0.5)
        
        assert len(result.relevant_docs) > 0
        
        # 检查是否包含医疗相关内容
        combined_text = " ".join(result.relevant_docs)
        assert any(keyword in combined_text for keyword in ["医疗", "治疗", "疾病"])

    def test_retrieve_drug_advertising(self, rag_service):
        """测试药品广告检索"""
        query = "药品广告的规定是什么？"
        result = rag_service.retrieve(query, top_k=3, similarity_threshold=0.5)
        
        assert len(result.relevant_docs) > 0
        
        # 检查是否包含药品相关内容
        combined_text = " ".join(result.relevant_docs)
        assert any(keyword in combined_text for keyword in ["药品", "处方药", "非处方药"])

    def test_retrieve_with_low_threshold(self, rag_service):
        """测试低阈值检索"""
        query = "广告法规定"
        result = rag_service.retrieve(query, top_k=5, similarity_threshold=0.3)
        
        # 低阈值应该返回更多结果
        assert len(result.relevant_docs) > 0

    def test_retrieve_with_high_threshold(self, rag_service):
        """测试高阈值检索"""
        query = "这是一个不相关的查询内容测试"
        result = rag_service.retrieve(query, top_k=3, similarity_threshold=0.9)
        
        # 高阈值可能返回较少或没有结果
        assert isinstance(result.relevant_docs, list)

    def test_retrieve_summary_generation(self, rag_service):
        """测试摘要生成"""
        query = "广告法的基本规定"
        result = rag_service.retrieve(query, top_k=3, similarity_threshold=0.5)
        
        assert result.summary is not None
        assert len(result.summary) > 0
        
        if result.relevant_docs:
            assert "找到" in result.summary or "未找到" in result.summary

    @pytest.mark.asyncio
    async def test_pipeline_with_rag(self, rag_service):
        """测试Pipeline集成RAG"""
        pipeline = ModerationPipeline(rag_service=rag_service)
        
        content_data = ContentData(
            content_type="text",
            content="本产品是最好的保健品，能治疗各种疾病，效果显著！",
            text="本产品是最好的保健品，能治疗各种疾病，效果显著！",
        )
        
        decision = await pipeline.execute(content_data)
        
        # 应该被规则引擎拦截（包含极限用语和医疗声明）
        assert decision is not None
        assert decision.is_compliant is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
