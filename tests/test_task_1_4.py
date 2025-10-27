"""Task 1.4: API路由设计 - 单元测试"""
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_root_endpoint():
    """测试根路径"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "version" in data


def test_health_check():
    """测试健康检查"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_submit_review():
    """测试提交审核"""
    request_data = {
        "content_type": "text",
        "content": "测试内容",
        "metadata": {"advertiser_id": "123"}
    }
    response = client.post("/api/v1/review", json=request_data)
    assert response.status_code == 200
    data = response.json()
    assert "task_id" in data
    assert data["status"] == "pending"
    assert "estimated_time" in data


def test_get_review_result():
    """测试查询审核结果"""
    # 先提交一个任务
    request_data = {
        "content_type": "text",
        "content": "测试内容"
    }
    submit_response = client.post("/api/v1/review", json=request_data)
    task_id = submit_response.json()["task_id"]
    
    # 查询结果
    response = client.get(f"/api/v1/review/{task_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["task_id"] == task_id


def test_get_review_result_not_found():
    """测试查询不存在的任务"""
    response = client.get("/api/v1/review/nonexistent-id")
    assert response.status_code == 404


def test_batch_review():
    """测试批量审核"""
    request_data = {
        "items": [
            {"content_type": "text", "content": "内容1"},
            {"content_type": "text", "content": "内容2"}
        ],
        "callback_url": "https://example.com/callback"
    }
    response = client.post("/api/v1/review/batch", json=request_data)
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 200
    assert "task_ids" in data["data"]
    assert len(data["data"]["task_ids"]) == 2


def test_get_stats():
    """测试获取统计信息"""
    response = client.get("/api/v1/stats")
    assert response.status_code == 200
    data = response.json()
    assert "total_reviews" in data
    assert "passed" in data
    assert "rejected" in data
    assert "accuracy" in data


def test_reload_rules():
    """测试重载规则"""
    response = client.post("/api/v1/admin/reload-rules")
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 200


def test_api_docs():
    """测试API文档"""
    response = client.get("/docs")
    assert response.status_code == 200
    
    response = client.get("/openapi.json")
    assert response.status_code == 200
