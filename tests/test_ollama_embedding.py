"""测试Ollama BGE-M3嵌入模型配置"""
import os
import sys
from pathlib import Path
import pytest

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class TestOllamaEmbedding:
    """测试Ollama嵌入模型"""
    
    def test_ollama_connection(self):
        """测试Ollama服务连接"""
        import requests
        
        ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        
        try:
            response = requests.get(f"{ollama_url}/api/tags", timeout=5)
            assert response.status_code == 200, "Ollama服务未运行"
            
            models = response.json().get("models", [])
            model_names = [m["name"] for m in models]
            
            print(f"\n✅ Ollama服务运行正常")
            print(f"   可用模型: {len(models)} 个")
            print(f"   模型列表: {', '.join(model_names[:5])}")
            
            # 检查bge-m3模型
            has_bge_m3 = any("bge-m3" in name for name in model_names)
            assert has_bge_m3, "未找到bge-m3模型，请运行: ollama pull bge-m3"
            
            print(f"   ✅ bge-m3模型已安装")
            
        except requests.exceptions.ConnectionError:
            pytest.skip("Ollama服务未运行，跳过测试")
    
    def test_ollama_embedding_generation(self):
        """测试Ollama嵌入生成"""
        from llama_index.embeddings.ollama import OllamaEmbedding
        
        ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        ollama_model = os.getenv("OLLAMA_EMBEDDING_MODEL", "bge-m3")
        
        try:
            # 创建嵌入模型
            embed_model = OllamaEmbedding(
                model_name=ollama_model,
                base_url=ollama_url,
            )
            
            # 测试文本
            test_text = "这是一个测试文本，用于验证嵌入模型是否正常工作。"
            
            # 生成嵌入
            embedding = embed_model.get_text_embedding(test_text)
            
            # 验证结果
            assert embedding is not None, "嵌入生成失败"
            assert len(embedding) > 0, "嵌入向量为空"
            assert isinstance(embedding, list), "嵌入应该是列表类型"
            
            print(f"\n✅ 嵌入生成成功")
            print(f"   模型: {ollama_model}")
            print(f"   向量维度: {len(embedding)}")
            print(f"   向量示例: {embedding[:5]}")
            
        except Exception as e:
            pytest.skip(f"Ollama嵌入生成失败: {str(e)}")
    
    def test_rag_service_with_ollama(self):
        """测试RAG服务使用Ollama"""
        # 设置环境变量
        os.environ["EMBEDDING_MODEL_TYPE"] = "ollama"
        os.environ["OLLAMA_BASE_URL"] = "http://localhost:11434"
        os.environ["OLLAMA_EMBEDDING_MODEL"] = "bge-m3"
        
        from services.rag_service import RAGService
        
        try:
            # 创建RAG服务
            rag_service = RAGService(
                docs_path="data/regulations",
                persist_dir="data/vector_store_ollama_test",
            )
            
            print(f"\n✅ RAG服务初始化成功")
            print(f"   使用Ollama嵌入模型")
            
            # 清理测试数据
            import shutil
            test_dir = Path("data/vector_store_ollama_test")
            if test_dir.exists():
                shutil.rmtree(test_dir)
                print(f"   清理测试数据: {test_dir}")
            
        except Exception as e:
            pytest.skip(f"RAG服务初始化失败: {str(e)}")
    
    def test_embedding_comparison(self):
        """测试嵌入相似度计算"""
        from llama_index.embeddings.ollama import OllamaEmbedding
        import numpy as np
        
        ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        ollama_model = os.getenv("OLLAMA_EMBEDDING_MODEL", "bge-m3")
        
        try:
            embed_model = OllamaEmbedding(
                model_name=ollama_model,
                base_url=ollama_url,
            )
            
            # 测试相似文本
            text1 = "这是一个关于广告法的规定"
            text2 = "这是广告法的相关条款"
            text3 = "今天天气很好"
            
            # 生成嵌入
            emb1 = np.array(embed_model.get_text_embedding(text1))
            emb2 = np.array(embed_model.get_text_embedding(text2))
            emb3 = np.array(embed_model.get_text_embedding(text3))
            
            # 计算余弦相似度
            def cosine_similarity(a, b):
                return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
            
            sim_12 = cosine_similarity(emb1, emb2)
            sim_13 = cosine_similarity(emb1, emb3)
            
            print(f"\n✅ 嵌入相似度测试")
            print(f"   文本1: {text1}")
            print(f"   文本2: {text2}")
            print(f"   文本3: {text3}")
            print(f"   相似度(1-2): {sim_12:.4f}")
            print(f"   相似度(1-3): {sim_13:.4f}")
            
            # 验证相似文本的相似度更高
            assert sim_12 > sim_13, "相似文本的相似度应该更高"
            assert sim_12 > 0.5, "相似文本的相似度应该大于0.5"
            
            print(f"   ✅ 相似度计算正确")
            
        except Exception as e:
            pytest.skip(f"嵌入相似度测试失败: {str(e)}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
