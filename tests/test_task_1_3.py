"""Task 1.3: LLM服务封装 - 单元测试"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from services.llm_service import LLMService, LLMResult


@pytest.fixture
def llm_service():
    """创建LLM服务实例（使用mock）"""
    return LLMService(
        deepseek_api_key="test_key",
        prompts_path="config/prompts.yaml"
    )


def test_llm_service_initialization(llm_service):
    """测试LLM服务初始化"""
    assert llm_service is not None
    assert llm_service.deepseek_api_key == "test_key"
    assert llm_service.prompts is not None


def test_load_prompts(llm_service):
    """测试Prompt模板加载"""
    assert "system" in llm_service.prompts
    assert "task" in llm_service.prompts
    assert len(llm_service.prompts["system"]) > 0


def test_select_model_light(llm_service):
    """测试轻量模型选择"""
    client, model_name, cost = llm_service._select_model("light")
    assert model_name == "deepseek-chat"
    assert cost == 0.00014


def test_select_model_strong(llm_service):
    """测试强模型选择"""
    # 只有DeepSeek可用时，strong也会使用DeepSeek
    client, model_name, cost = llm_service._select_model("strong")
    assert model_name == "deepseek-chat"


@patch('services.llm_service.OpenAI')
def test_review_content_mock(mock_openai, llm_service):
    """测试内容审核（使用mock）"""
    # Mock API响应
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = '''
    {
        "is_compliant": false,
        "violation_types": ["extreme_language"],
        "evidence": "包含绝对化用语",
        "confidence": 0.95,
        "reasoning": "违反广告法第9条"
    }
    '''
    mock_response.usage.total_tokens = 500
    
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = mock_response
    llm_service.deepseek_client = mock_client
    
    # 执行审核
    result = llm_service.review_content(
        content="我们是最好的产品",
        regulations="广告法第9条"
    )
    
    assert isinstance(result, LLMResult)
    assert result.is_compliant is False
    assert "extreme_language" in result.violation_types
    assert result.confidence == 0.95
    assert result.tokens_used == 500


def test_get_statistics(llm_service):
    """测试统计信息"""
    stats = llm_service.get_statistics()
    assert "total_tokens_used" in stats
    assert "total_api_cost" in stats
    assert "deepseek_available" in stats
    assert stats["deepseek_available"] is True


def test_prompt_formatting(llm_service):
    """测试Prompt格式化"""
    task_prompt = llm_service.prompts["task"].format(
        content="测试内容",
        regulations="测试法规"
    )
    assert "测试内容" in task_prompt
    assert "测试法规" in task_prompt
