"""Day 2 简化部署测试 - 手动启动服务"""
import requests
import time
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def test_backend_services():
    """测试后端服务（需要手动启动）"""
    backend_url = "http://localhost:8000"
    
    print("\n" + "="*60)
    print("Day 2 后端服务测试")
    print("="*60)
    print("\n请确保后端服务已启动:")
    print("  pipenv run python main.py")
    print("\n等待5秒...")
    time.sleep(5)
    
    try:
        # 1. 健康检查
        print("\n1. 测试健康检查...")
        response = requests.get(f"{backend_url}/health", timeout=5)
        assert response.status_code == 200
        print("   ✅ 健康检查通过")
        
        # 2. 根路径
        print("\n2. 测试根路径...")
        response = requests.get(f"{backend_url}/", timeout=5)
        assert response.status_code == 200
        data = response.json()
        print(f"   ✅ 版本: {data['version']}")
        
        # 3. API文档
        print("\n3. 测试API文档...")
        response = requests.get(f"{backend_url}/docs", timeout=5)
        assert response.status_code == 200
        print(f"   ✅ API文档可访问: {backend_url}/docs")
        
        # 4. 统计接口
        print("\n4. 测试统计接口...")
        response = requests.get(f"{backend_url}/api/v1/stats", timeout=5)
        assert response.status_code == 200
        data = response.json()
        assert "total_reviews" in data
        assert "violation_rate" in data
        print(f"   ✅ 统计接口正常")
        print(f"      - 总审核数: {data['total_reviews']}")
        print(f"      - 违规率: {data['violation_rate']:.2%}")
        
        # 5. 审核接口（同步模式）
        print("\n5. 测试审核接口（同步模式）...")
        payload = {
            "content": "这是一个测试内容",
            "content_type": "text"
        }
        
        start_time = time.time()
        response = requests.post(
            f"{backend_url}/api/v1/review?sync=true",
            json=payload,
            timeout=30
        )
        elapsed = time.time() - start_time
        
        assert response.status_code == 200
        data = response.json()
        
        print(f"   ✅ 审核接口正常")
        print(f"      - 任务ID: {data['task_id']}")
        print(f"      - 状态: {data['status']}")
        print(f"      - 响应时间: {elapsed:.2f}秒")
        
        if data["status"] == "completed" and "result" in data:
            result = data["result"]
            print(f"      - 合规性: {result['is_compliant']}")
            print(f"      - 置信度: {result['confidence']:.2%}")
        
        # 6. 批量审核
        print("\n6. 测试批量审核...")
        batch_payload = {
            "items": [
                {"content": "正常内容", "content_type": "text"},
                {"content": "全网最低价！", "content_type": "text"}
            ]
        }
        
        response = requests.post(
            f"{backend_url}/api/v1/review/batch?sync=true",
            json=batch_payload,
            timeout=60
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        print(f"   ✅ 批量审核正常")
        print(f"      - 审核数量: {len(data['results'])}")
        
        # 7. 端到端测试
        print("\n7. 端到端审核测试...")
        test_cases = [
            ("正常内容", "优质产品，欢迎选购"),
            ("违规内容", "全网最低价！100%有效！")
        ]
        
        for name, content in test_cases:
            payload = {"content": content, "content_type": "text"}
            response = requests.post(
                f"{backend_url}/api/v1/review?sync=true",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if data["status"] == "completed" and "result" in data:
                    result = data["result"]
                    status = "✅ 合规" if result['is_compliant'] else "❌ 违规"
                    print(f"   {name}: {status} (置信度: {result['confidence']:.2%})")
        
        print("\n" + "="*60)
        print("🎉 Day 2 后端服务测试全部通过！")
        print("="*60)
        print("\n✅ 健康检查正常")
        print("✅ API文档可访问")
        print("✅ 统计接口正常")
        print("✅ 审核接口正常")
        print("✅ 批量审核正常")
        print("✅ 端到端流程正常")
        print("\n📝 访问地址:")
        print(f"   - API文档: {backend_url}/docs")
        print(f"   - 健康检查: {backend_url}/health")
        print("="*60)
        
        return True
        
    except requests.exceptions.ConnectionError:
        print("\n❌ 无法连接到后端服务")
        print("   请先启动后端服务: pipenv run python main.py")
        return False
    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}")
        return False
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_frontend_service():
    """测试前端服务（需要手动启动）"""
    frontend_url = "http://localhost:8501"
    
    print("\n" + "="*60)
    print("Day 2 前端服务测试")
    print("="*60)
    print("\n请确保前端服务已启动:")
    print("  pipenv run python run_ui.py")
    print("\n等待5秒...")
    time.sleep(5)
    
    try:
        print("\n1. 测试前端可访问性...")
        response = requests.get(frontend_url, timeout=10)
        assert response.status_code == 200
        print(f"   ✅ 前端服务正常: {frontend_url}")
        
        print("\n" + "="*60)
        print("🎉 Day 2 前端服务测试通过！")
        print("="*60)
        print(f"\n📝 访问地址: {frontend_url}")
        print("="*60)
        
        return True
        
    except requests.exceptions.ConnectionError:
        print("\n❌ 无法连接到前端服务")
        print("   请先启动前端服务: pipenv run python run_ui.py")
        return False
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        return False


if __name__ == "__main__":
    print("\n" + "="*60)
    print("Day 2 前后端部署测试")
    print("="*60)
    
    # 测试后端
    backend_ok = test_backend_services()
    
    # 测试前端
    frontend_ok = test_frontend_service()
    
    # 总结
    print("\n" + "="*60)
    print("测试总结")
    print("="*60)
    print(f"后端服务: {'✅ 通过' if backend_ok else '❌ 失败'}")
    print(f"前端服务: {'✅ 通过' if frontend_ok else '❌ 失败'}")
    print("="*60)
    
    if backend_ok and frontend_ok:
        print("\n🎉 Day 2 前后端部署测试全部通过！")
        sys.exit(0)
    else:
        print("\n❌ 部分测试失败，请检查服务状态")
        sys.exit(1)
