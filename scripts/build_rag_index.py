"""构建RAG向量索引脚本"""
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.rag_service import RAGService


def main():
    """构建索引主函数"""
    print("=" * 60)
    print("开始构建RAG向量索引")
    print("=" * 60)
    
    # 初始化RAG服务
    rag = RAGService(
        docs_path="data/regulations",
        persist_dir="data/vector_store",
        collection_name="regulations",
        chunk_size=512,
        chunk_overlap=50,
    )
    
    # 构建索引
    try:
        stats = rag.build_index(force_rebuild=True)
        
        print("\n" + "=" * 60)
        print("索引构建完成！")
        print("=" * 60)
        print(f"总文档数: {stats['total_documents']}")
        print(f"总文本块数: {stats['total_chunks']}")
        print(f"集合名称: {stats['collection_name']}")
        print(f"存储路径: {stats['persist_dir']}")
        print("=" * 60)
        
        # 测试检索
        print("\n测试检索功能...")
        test_queries = [
            "广告中不能使用哪些极限用语？",
            "医疗广告有什么限制？",
            "药品广告的要求是什么？",
        ]
        
        for query in test_queries:
            print(f"\n查询: {query}")
            result = rag.retrieve(query, top_k=3, similarity_threshold=0.5)
            print(f"找到 {len(result.relevant_docs)} 条相关文档")
            if result.relevant_docs:
                print(f"最高相似度: {max(result.scores):.3f}")
                print(f"摘要: {result.summary[:200]}...")
        
        print("\n" + "=" * 60)
        print("测试完成！")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
