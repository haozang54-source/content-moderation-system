"""审核流程编排"""
from typing import Optional, Dict
from dataclasses import dataclass
from datetime import datetime

from services.rule_engine import RuleEngine
from services.ocr_service import OCRService
from services.llm_service import LLMService
from config.settings import settings


@dataclass
class ContentData:
    """内容数据"""
    content_type: str
    content: str
    text: str = ""
    metadata: Dict = None


@dataclass
class Decision:
    """审核决策"""
    is_compliant: bool
    violation_types: list
    evidence: str
    confidence: float
    reasoning: str
    need_human_review: bool
    stage: str
    costs: Dict


class ModerationPipeline:
    """审核流程编排器"""

    def __init__(
        self,
        rule_engine: Optional[RuleEngine] = None,
        ocr_service: Optional[OCRService] = None,
        llm_service: Optional[LLMService] = None
    ):
        """初始化Pipeline
        
        Args:
            rule_engine: 规则引擎
            ocr_service: OCR服务
            llm_service: LLM服务
        """
        self.rule_engine = rule_engine or RuleEngine()
        self.ocr_service = ocr_service or OCRService()
        self.llm_service = llm_service or LLMService(
            deepseek_api_key=settings.deepseek_api_key,
            openai_api_key=settings.openai_api_key
        )
        
        self.confidence_threshold_high = settings.confidence_threshold_high
        self.confidence_threshold_low = settings.confidence_threshold_low

    async def execute(self, content_data: ContentData) -> Decision:
        """执行审核流程
        
        Args:
            content_data: 内容数据
            
        Returns:
            Decision: 审核决策
        """
        start_time = datetime.now()
        
        # Stage 1: 规则引擎预筛
        rule_result = self.rule_engine.check_text(content_data.content)
        
        if rule_result.is_violated:
            # 规则命中，直接拒绝
            return Decision(
                is_compliant=False,
                violation_types=rule_result.violation_types,
                evidence=rule_result.evidence,
                confidence=1.0,
                reasoning="规则引擎命中黑名单",
                need_human_review=False,
                stage="rule_engine",
                costs={"tokens_used": 0, "api_cost": 0.0}
            )

        # Stage 2: OCR提取（如果是图像）
        if content_data.content_type == "image":
            try:
                extracted_text = await self.ocr_service.extract_text_multi_engine(
                    content_data.content
                )
                content_data.text += " " + extracted_text
            except Exception as e:
                print(f"OCR提取失败: {e}")

        # 如果没有文本内容，无法审核
        if not content_data.text and not content_data.content:
            return Decision(
                is_compliant=True,
                violation_types=[],
                evidence="",
                confidence=0.5,
                reasoning="无文本内容可审核",
                need_human_review=True,
                stage="ocr",
                costs={"tokens_used": 0, "api_cost": 0.0}
            )

        # Stage 3: RAG检索（暂时跳过，使用空字符串）
        regulations = ""

        # Stage 4: LLM审核（分层调用）
        review_text = content_data.text or content_data.content
        
        try:
            # 先用轻量模型
            llm_result = self.llm_service.review_content(
                content=review_text,
                regulations=regulations,
                model_type="light"
            )
            
            # Stage 5: 置信度分流
            if llm_result.confidence >= self.confidence_threshold_high:
                # 高置信度，自动判决
                return Decision(
                    is_compliant=llm_result.is_compliant,
                    violation_types=llm_result.violation_types,
                    evidence=llm_result.evidence,
                    confidence=llm_result.confidence,
                    reasoning=llm_result.reasoning,
                    need_human_review=False,
                    stage="llm_light",
                    costs={
                        "tokens_used": llm_result.tokens_used,
                        "api_cost": llm_result.api_cost
                    }
                )
            
            elif llm_result.confidence < self.confidence_threshold_low:
                # 低置信度，调用强模型
                strong_result = self.llm_service.review_content(
                    content=review_text,
                    regulations=regulations,
                    model_type="strong"
                )
                
                return Decision(
                    is_compliant=strong_result.is_compliant,
                    violation_types=strong_result.violation_types,
                    evidence=strong_result.evidence,
                    confidence=strong_result.confidence,
                    reasoning=strong_result.reasoning,
                    need_human_review=strong_result.confidence < self.confidence_threshold_low,
                    stage="llm_strong",
                    costs={
                        "tokens_used": llm_result.tokens_used + strong_result.tokens_used,
                        "api_cost": llm_result.api_cost + strong_result.api_cost
                    }
                )
            
            else:
                # 中等置信度，转人工复审
                return Decision(
                    is_compliant=llm_result.is_compliant,
                    violation_types=llm_result.violation_types,
                    evidence=llm_result.evidence,
                    confidence=llm_result.confidence,
                    reasoning=llm_result.reasoning,
                    need_human_review=True,
                    stage="llm_light",
                    costs={
                        "tokens_used": llm_result.tokens_used,
                        "api_cost": llm_result.api_cost
                    }
                )
        
        except Exception as e:
            # 异常兜底，转人工
            print(f"LLM审核失败: {e}")
            return Decision(
                is_compliant=True,
                violation_types=[],
                evidence="",
                confidence=0.0,
                reasoning=f"系统异常: {str(e)}",
                need_human_review=True,
                stage="error",
                costs={"tokens_used": 0, "api_cost": 0.0}
            )

    def get_statistics(self) -> Dict:
        """获取统计信息
        
        Returns:
            Dict: 统计信息
        """
        return {
            "rule_engine": self.rule_engine.get_statistics(),
            "ocr_service": self.ocr_service.get_statistics(),
            "llm_service": self.llm_service.get_statistics()
        }
