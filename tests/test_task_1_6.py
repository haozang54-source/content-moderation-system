"""Task 1.6: 审核流程编排 - 单元测试"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from core.pipeline import ModerationPipeline, ContentData, Decision
from services.rule_engine import RuleEngine, RuleResult
from services.ocr_service import OCRService
from services.llm_service import LLMService, LLMResult


@pytest.fixture
def mock_rule_engine():
    """Mock规则引擎"""
    engine = Mock(spec=RuleEngine)
    engine.check_text.return_value = RuleResult(
        is_violated=False,
        violation_types=[],
        matched_keywords=[],
        matched_positions=[],
        severity="none",
        evidence=""
    )
    engine.get_statistics.return_value = {"total_rules": 10}
    return engine


@pytest.fixture
def mock_ocr_service():
    """Mock OCR服务"""
    service = Mock(spec=OCRService)
    service.extract_text_multi_engine = AsyncMock(return_value="提取的文本")
    service.get_statistics.return_value = {"paddle_available": True}
    return service


@pytest.fixture
def mock_llm_service():
    """Mock LLM服务"""
    service = Mock(spec=LLMService)
    service.review_content.return_value = LLMResult(
        is_compliant=True,
        violation_types=[],
        evidence="",
        confidence=0.95,
        reasoning="内容合规",
        tokens_used=100,
        api_cost=0.001
    )
    service.get_statistics.return_value = {"total_tokens_used": 100}
    return service


@pytest.fixture
def pipeline(mock_rule_engine, mock_ocr_service, mock_llm_service):
    """创建Pipeline实例"""
    return ModerationPipeline(
        rule_engine=mock_rule_engine,
        ocr_service=mock_ocr_service,
        llm_service=mock_llm_service
    )


@pytest.mark.asyncio
async def test_pipeline_rule_engine_hit(pipeline, mock_rule_engine):
    """测试规则引擎命中场景"""
    # 设置规则引擎返回违规
    mock_rule_engine.check_text.return_value = RuleResult(
        is_violated=True,
        violation_types=["extreme_language"],
        matched_keywords=["最好"],
        matched_positions=[(0, 2)],
        severity="high",
        evidence="包含极限用语"
    )
    
    content = ContentData(
        content_type="text",
        content="这是最好的产品"
    )
    
    decision = await pipeline.execute(content)
    
    assert decision.is_compliant is False
    assert "extreme_language" in decision.violation_types
    assert decision.stage == "rule_engine"
    assert decision.confidence == 1.0


@pytest.mark.asyncio
async def test_pipeline_high_confidence(pipeline, mock_llm_service):
    """测试高置信度场景"""
    mock_llm_service.review_content.return_value = LLMResult(
        is_compliant=True,
        violation_types=[],
        evidence="",
        confidence=0.95,
        reasoning="内容合规",
        tokens_used=100,
        api_cost=0.001
    )
    
    content = ContentData(
        content_type="text",
        content="这是正常的广告文案"
    )
    
    decision = await pipeline.execute(content)
    
    assert decision.confidence >= 0.9
    assert decision.need_human_review is False
    assert decision.stage == "llm_light"


@pytest.mark.asyncio
async def test_pipeline_low_confidence(pipeline, mock_llm_service):
    """测试低置信度场景（触发强模型）"""
    # 第一次调用返回低置信度
    mock_llm_service.review_content.side_effect = [
        LLMResult(
            is_compliant=True,
            violation_types=[],
            evidence="",
            confidence=0.5,
            reasoning="不确定",
            tokens_used=100,
            api_cost=0.001
        ),
        # 第二次调用（强模型）返回高置信度
        LLMResult(
            is_compliant=True,
            violation_types=[],
            evidence="",
            confidence=0.92,
            reasoning="确认合规",
            tokens_used=200,
            api_cost=0.006
        )
    ]
    
    content = ContentData(
        content_type="text",
        content="边界case内容"
    )
    
    decision = await pipeline.execute(content)
    
    assert decision.stage == "llm_strong"
    assert decision.costs["tokens_used"] == 300  # 两次调用总和


@pytest.mark.asyncio
async def test_pipeline_medium_confidence(pipeline, mock_llm_service):
    """测试中等置信度场景（转人工）"""
    mock_llm_service.review_content.return_value = LLMResult(
        is_compliant=True,
        violation_types=[],
        evidence="",
        confidence=0.75,
        reasoning="可能合规",
        tokens_used=100,
        api_cost=0.001
    )
    
    content = ContentData(
        content_type="text",
        content="模糊内容"
    )
    
    decision = await pipeline.execute(content)
    
    assert decision.need_human_review is True
    assert 0.6 <= decision.confidence < 0.9


@pytest.mark.asyncio
async def test_pipeline_image_content(pipeline, mock_ocr_service):
    """测试图像内容处理"""
    content = ContentData(
        content_type="image",
        content="image_url.jpg"
    )
    
    decision = await pipeline.execute(content)
    
    # 验证OCR被调用
    mock_ocr_service.extract_text_multi_engine.assert_called_once()


@pytest.mark.asyncio
async def test_pipeline_empty_content(pipeline):
    """测试空内容"""
    content = ContentData(
        content_type="text",
        content=""
    )
    
    decision = await pipeline.execute(content)
    
    assert decision.need_human_review is True
    assert decision.confidence == 0.5


@pytest.mark.asyncio
async def test_pipeline_exception_handling(pipeline, mock_llm_service):
    """测试异常处理"""
    mock_llm_service.review_content.side_effect = Exception("API错误")
    
    content = ContentData(
        content_type="text",
        content="测试内容"
    )
    
    decision = await pipeline.execute(content)
    
    assert decision.need_human_review is True
    assert decision.stage == "error"
    assert "系统异常" in decision.reasoning


def test_pipeline_get_statistics(pipeline):
    """测试统计信息"""
    stats = pipeline.get_statistics()
    
    assert "rule_engine" in stats
    assert "ocr_service" in stats
    assert "llm_service" in stats
