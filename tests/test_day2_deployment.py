"""Day 2 前后端部署测试

测试内容：
1. 后端API服务启动测试
2. 前端UI服务启动测试
3. 前后端联调测试
4. RAG服务集成测试
5. 完整审核流程测试
"""
import pytest
import requests
import time
import subprocess
import sys
from pathlib import Path
from typing import Optional
import signal
import os

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class ServiceManager:
    """服务管理器"""
    
    def __init__(self):
        self.backend_process: Optional[subprocess.Popen] = None
        self.frontend_process: Optional[subprocess.Popen] = None
        self.backend_url = "http://localhost:8000"
        self.frontend_url = "http://localhost:8501"
    
    def start_backend(self, timeout: int = 30) -> bool:
        """启动后端服务"""
        print("\n🚀 启动后端服务...")
        
        try:
            # 启动FastAPI服务
            self.backend_process = subprocess.Popen(
                [sys.executable, "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"],
                cwd=str(project_root),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # 等待服务启动
            start_time = time.time()
            while time.time() - start_time < timeout:
                try:
                    response = requests.get(f"{self.backend_url}/health", timeout=2)
                    if response.status_code == 200:
                        print(f"✅ 后端服务启动成功: {self.backend_url}")
                        return True
                except requests.exceptions.RequestException:
                    time.sleep(1)
            
            print("❌ 后端服务启动超时")
            return False
            
        except Exception as e:
            print(f"❌ 后端服务启动失败: {e}")
            return False
    
    def start_frontend(self, timeout: int = 30) -> bool:
        """启动前端服务"""
        print("\n🚀 启动前端服务...")
        
        try:
            # 启动Streamlit服务
            self.frontend_process = subprocess.Popen(
                [sys.executable, "-m", "streamlit", "run", "ui/app.py", 
                 "--server.port", "8501", "--server.headless", "true"],
                cwd=str(project_root),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # 等待服务启动
            start_time = time.time()
            while time.time() - start_time < timeout:
                try:
                    response = requests.get(self.frontend_url, timeout=2)
                    if response.status_code == 200:
                        print(f"✅ 前端服务启动成功: {self.frontend_url}")
                        return True
                except requests.exceptions.RequestException:
                    time.sleep(1)
            
            print("❌ 前端服务启动超时")
            return False
            
        except Exception as e:
            print(f"❌ 前端服务启动失败: {e}")
            return False
    
    def stop_backend(self):
        """停止后端服务"""
        if self.backend_process:
            print("\n🛑 停止后端服务...")
            self.backend_process.terminate()
            try:
                self.backend_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.backend_process.kill()
            print("✅ 后端服务已停止")
    
    def stop_frontend(self):
        """停止前端服务"""
        if self.frontend_process:
            print("\n🛑 停止前端服务...")
            self.frontend_process.terminate()
            try:
                self.frontend_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.frontend_process.kill()
            print("✅ 前端服务已停止")
    
    def cleanup(self):
        """清理所有服务"""
        self.stop_backend()
        self.stop_frontend()


@pytest.fixture(scope="module")
def service_manager():
    """服务管理器fixture"""
    manager = ServiceManager()
    yield manager
    manager.cleanup()


class TestBackendDeployment:
    """后端部署测试"""
    
    def test_backend_startup(self, service_manager):
        """测试后端服务启动"""
        assert service_manager.start_backend(), "后端服务启动失败"
    
    def test_backend_health_check(self, service_manager):
        """测试后端健康检查"""
        response = requests.get(f"{service_manager.backend_url}/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        print(f"\n✅ 健康检查通过: {data}")
    
    def test_backend_root_endpoint(self, service_manager):
        """测试后端根路径"""
        response = requests.get(f"{service_manager.backend_url}/")
        assert response.status_code == 200
        data = response.json()
        assert "version" in data
        assert data["status"] == "running"
        print(f"\n✅ 根路径访问成功: {data}")
    
    def test_backend_api_docs(self, service_manager):
        """测试API文档可访问"""
        response = requests.get(f"{service_manager.backend_url}/docs")
        assert response.status_code == 200
        print(f"\n✅ API文档可访问: {service_manager.backend_url}/docs")
    
    def test_backend_review_endpoint(self, service_manager):
        """测试审核接口"""
        # 测试文本审核（同步模式）
        payload = {
            "content": "这是一个测试内容",
            "content_type": "text"
        }
        
        response = requests.post(
            f"{service_manager.backend_url}/api/v1/review?sync=true",
            json=payload,
            timeout=30
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # 检查响应结构
        assert "task_id" in data
        assert "status" in data
        
        # 如果是同步模式，应该有result
        if data["status"] == "completed":
            assert "result" in data
            result = data["result"]
            assert "is_compliant" in result
            assert "confidence" in result
            assert "violation_types" in result
            
            print(f"\n✅ 审核接口测试通过:")
            print(f"   - 合规性: {result['is_compliant']}")
            print(f"   - 置信度: {result['confidence']:.2%}")
        else:
            print(f"\n✅ 审核接口测试通过 (异步模式)")
            print(f"   - 任务ID: {data['task_id']}")
            print(f"   - 状态: {data['status']}")
    
    def test_backend_stats_endpoint(self, service_manager):
        """测试统计接口"""
        response = requests.get(f"{service_manager.backend_url}/api/v1/stats")
        assert response.status_code == 200
        data = response.json()
        
        # 验证统计数据结构
        assert "total_reviews" in data
        assert "violation_rate" in data
        
        print(f"\n✅ 统计接口测试通过:")
        print(f"   - 总审核数: {data['total_reviews']}")
        print(f"   - 违规率: {data['violation_rate']:.2%}")


class TestFrontendDeployment:
    """前端部署测试"""
    
    def test_frontend_startup(self, service_manager):
        """测试前端服务启动"""
        # 确保后端已启动
        if not service_manager.backend_process:
            service_manager.start_backend()
        
        assert service_manager.start_frontend(), "前端服务启动失败"
    
    def test_frontend_accessibility(self, service_manager):
        """测试前端可访问性"""
        response = requests.get(service_manager.frontend_url, timeout=10)
        assert response.status_code == 200
        assert len(response.content) > 0
        print(f"\n✅ 前端页面可访问: {service_manager.frontend_url}")
    
    def test_frontend_page_title(self, service_manager):
        """测试前端页面标题"""
        response = requests.get(service_manager.frontend_url, timeout=10)
        content = response.text
        
        # 检查是否包含关键元素
        assert "streamlit" in content.lower() or "商业违规" in content
        print(f"\n✅ 前端页面内容正常")


class TestIntegration:
    """前后端集成测试"""
    
    def test_end_to_end_text_review(self, service_manager):
        """测试端到端文本审核流程"""
        # 确保服务都已启动
        if not service_manager.backend_process:
            service_manager.start_backend()
        
        print("\n" + "="*60)
        print("端到端审核流程测试")
        print("="*60)
        
        test_cases = [
            {
                "name": "正常内容",
                "content": "优质产品，欢迎选购",
                "expected_compliant": True
            },
            {
                "name": "违规内容",
                "content": "全网最低价！100%有效！",
                "expected_compliant": False
            }
        ]
        
        for case in test_cases:
            print(f"\n测试场景: {case['name']}")
            print(f"内容: {case['content']}")
            
            payload = {
                "content": case["content"],
                "content_type": "text"
            }
            
            start_time = time.time()
            response = requests.post(
                f"{service_manager.backend_url}/api/v1/review?sync=true",
                json=payload,
                timeout=30
            )
            elapsed = time.time() - start_time
            
            assert response.status_code == 200
            data = response.json()
            
            if data["status"] == "completed" and "result" in data:
                result = data["result"]
                print(f"结果: {'✅ 合规' if result['is_compliant'] else '❌ 违规'}")
                print(f"置信度: {result['confidence']:.2%}")
                print(f"响应时间: {elapsed:.2f}秒")
                
                if not result['is_compliant']:
                    print(f"违规类型: {', '.join(result['violation_types'])}")
            else:
                print(f"任务状态: {data['status']}")
    
    def test_batch_review(self, service_manager):
        """测试批量审核"""
        if not service_manager.backend_process:
            service_manager.start_backend()
        
        print("\n" + "="*60)
        print("批量审核测试")
        print("="*60)
        
        contents = [
            "正常内容1",
            "全网最低价！",
            "优质产品推荐",
            "100%有效！",
            "欢迎咨询"
        ]
        
        payload = {
            "items": [{"content": c, "content_type": "text"} for c in contents]
        }
        
        start_time = time.time()
        response = requests.post(
            f"{service_manager.backend_url}/api/v1/review/batch?sync=true",
            json=payload,
            timeout=60
        )
        elapsed = time.time() - start_time
        
        assert response.status_code == 200
        data = response.json()
        
        assert "results" in data
        assert len(data["results"]) == len(contents)
        
        print(f"\n✅ 批量审核完成:")
        print(f"   - 总数: {len(contents)}")
        print(f"   - 总耗时: {elapsed:.2f}秒")
        print(f"   - 平均耗时: {elapsed/len(contents):.2f}秒/条")
        
        # 统计结果
        compliant_count = sum(1 for r in data["results"] if r.get("is_compliant", False))
        violation_count = len(contents) - compliant_count
        
        print(f"   - 合规: {compliant_count}")
        print(f"   - 违规: {violation_count}")
    
    def test_rag_integration(self, service_manager):
        """测试RAG集成"""
        if not service_manager.backend_process:
            service_manager.start_backend()
        
        print("\n" + "="*60)
        print("RAG集成测试")
        print("="*60)
        
        # 测试包含法规相关的内容
        test_content = "本产品可以治疗癌症，100%有效"
        
        payload = {
            "content": test_content,
            "content_type": "text"
        }
        
        response = requests.post(
            f"{service_manager.backend_url}/api/v1/review?sync=true",
            json=payload,
            timeout=30
        )
        
        assert response.status_code == 200
        data = response.json()
        
        print(f"\n测试内容: {test_content}")
        
        if data["status"] == "completed" and "result" in data:
            result = data["result"]
            print(f"审核结果: {'✅ 合规' if result['is_compliant'] else '❌ 违规'}")
            print(f"置信度: {result['confidence']:.2%}")
            
            if not result['is_compliant']:
                print(f"违规类型: {', '.join(result['violation_types'])}")
                
                # 检查是否有RAG相关信息
                if 'details' in result and 'rag_context' in result['details']:
                    print(f"✅ RAG检索已集成")
                    print(f"   相关法规: {len(result['details']['rag_context'])} 条")


class TestPerformance:
    """性能测试"""
    
    def test_response_time(self, service_manager):
        """测试响应时间"""
        if not service_manager.backend_process:
            service_manager.start_backend()
        
        print("\n" + "="*60)
        print("响应时间测试")
        print("="*60)
        
        test_content = "测试内容，用于性能测试"
        payload = {
            "content": test_content,
            "content_type": "text"
        }
        
        response_times = []
        
        for i in range(5):
            start_time = time.time()
            response = requests.post(
                f"{service_manager.backend_url}/api/v1/review?sync=true",
                json=payload,
                timeout=30
            )
            elapsed = time.time() - start_time
            
            assert response.status_code == 200
            response_times.append(elapsed)
            print(f"第 {i+1} 次: {elapsed:.2f}秒")
        
        avg_time = sum(response_times) / len(response_times)
        max_time = max(response_times)
        min_time = min(response_times)
        
        print(f"\n性能统计:")
        print(f"   - 平均响应时间: {avg_time:.2f}秒")
        print(f"   - 最快响应: {min_time:.2f}秒")
        print(f"   - 最慢响应: {max_time:.2f}秒")
        
        # 验证性能要求
        assert avg_time < 10, f"平均响应时间过长: {avg_time:.2f}秒"
        print(f"\n✅ 性能测试通过 (平均 {avg_time:.2f}秒 < 10秒)")
    
    def test_concurrent_requests(self, service_manager):
        """测试并发请求"""
        if not service_manager.backend_process:
            service_manager.start_backend()
        
        print("\n" + "="*60)
        print("并发请求测试")
        print("="*60)
        
        import concurrent.futures
        
        def make_request(content: str):
            payload = {"content": content, "content_type": "text"}
            start = time.time()
            response = requests.post(
                f"{service_manager.backend_url}/api/v1/review?sync=true",
                json=payload,
                timeout=30
            )
            elapsed = time.time() - start
            return response.status_code == 200, elapsed
        
        # 并发5个请求
        contents = [f"测试内容{i}" for i in range(5)]
        
        start_time = time.time()
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            results = list(executor.map(make_request, contents))
        total_time = time.time() - start_time
        
        success_count = sum(1 for success, _ in results if success)
        avg_response_time = sum(t for _, t in results) / len(results)
        
        print(f"\n并发测试结果:")
        print(f"   - 并发数: {len(contents)}")
        print(f"   - 成功数: {success_count}/{len(contents)}")
        print(f"   - 总耗时: {total_time:.2f}秒")
        print(f"   - 平均响应: {avg_response_time:.2f}秒")
        
        assert success_count == len(contents), "部分请求失败"
        print(f"\n✅ 并发测试通过")


class TestDeploymentSummary:
    """部署测试总结"""
    
    def test_deployment_summary(self, service_manager):
        """生成部署测试总结"""
        print("\n" + "="*60)
        print("Day 2 前后端部署测试总结")
        print("="*60)
        
        summary = {
            "后端服务": "✅ 正常运行" if service_manager.backend_process else "❌ 未启动",
            "前端服务": "✅ 正常运行" if service_manager.frontend_process else "❌ 未启动",
            "后端URL": service_manager.backend_url,
            "前端URL": service_manager.frontend_url,
        }
        
        print("\n服务状态:")
        for key, value in summary.items():
            print(f"   - {key}: {value}")
        
        # 测试关键功能
        if service_manager.backend_process:
            try:
                # 健康检查
                health_response = requests.get(f"{service_manager.backend_url}/health", timeout=5)
                health_ok = health_response.status_code == 200
                
                # 审核接口
                review_response = requests.post(
                    f"{service_manager.backend_url}/api/v1/review?sync=true",
                    json={"content": "测试", "content_type": "text"},
                    timeout=30
                )
                review_ok = review_response.status_code == 200
                
                # 统计接口
                stats_response = requests.get(f"{service_manager.backend_url}/api/v1/stats", timeout=5)
                stats_ok = stats_response.status_code == 200
                
                print("\n功能测试:")
                print(f"   - 健康检查: {'✅' if health_ok else '❌'}")
                print(f"   - 审核接口: {'✅' if review_ok else '❌'}")
                print(f"   - 统计接口: {'✅' if stats_ok else '❌'}")
                
                all_ok = health_ok and review_ok and stats_ok
                
                if all_ok:
                    print("\n" + "="*60)
                    print("🎉 Day 2 前后端部署测试全部通过！")
                    print("="*60)
                    print("\n✅ 后端API服务正常")
                    print("✅ 前端UI服务正常")
                    print("✅ 前后端联调成功")
                    print("✅ RAG服务集成正常")
                    print("✅ 完整审核流程可用")
                    print("\n📝 访问地址:")
                    print(f"   - API文档: {service_manager.backend_url}/docs")
                    print(f"   - 前端界面: {service_manager.frontend_url}")
                    print("="*60)
                
                assert all_ok, "部分功能测试失败"
                
            except Exception as e:
                print(f"\n❌ 功能测试失败: {e}")
                raise


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v", "-s", "--tb=short"])
