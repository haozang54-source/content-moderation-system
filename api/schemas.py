"""API数据模型"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime
from enum import Enum


class ContentType(str, Enum):
    """内容类型"""
    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"


class ReviewRequest(BaseModel):
    """审核请求"""
    content_type: ContentType = Field(..., description="内容类型")
    content: str = Field(..., description="文本内容或URL")
    metadata: Optional[Dict] = Field(default={}, description="元数据")


class ReviewStatus(str, Enum):
    """审核状态"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ReviewResult(BaseModel):
    """审核结果"""
    is_compliant: bool = Field(..., description="是否合规")
    violation_types: List[str] = Field(default=[], description="违规类型")
    evidence: str = Field(default="", description="违规证据")
    confidence: float = Field(..., description="置信度")
    reasoning: str = Field(default="", description="判断理由")
    regulations: Optional[List[Dict]] = Field(default=None, description="相关法规")
    need_human_review: bool = Field(default=False, description="是否需要人工复审")


class ReviewResponse(BaseModel):
    """审核响应"""
    task_id: str = Field(..., description="任务ID")
    status: ReviewStatus = Field(..., description="任务状态")
    result: Optional[ReviewResult] = Field(default=None, description="审核结果")
    costs: Optional[Dict] = Field(default=None, description="成本信息")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    completed_at: Optional[datetime] = Field(default=None, description="完成时间")
    estimated_time: Optional[int] = Field(default=None, description="预计完成时间（秒）")


class BatchReviewRequest(BaseModel):
    """批量审核请求"""
    items: List[ReviewRequest] = Field(..., description="审核项列表")
    callback_url: Optional[str] = Field(default=None, description="回调URL")


class StatsResponse(BaseModel):
    """统计响应"""
    total_reviews: int = Field(..., description="总审核数")
    passed: int = Field(..., description="通过数")
    rejected: int = Field(..., description="拒绝数")
    human_review: int = Field(..., description="人工复审数")
    accuracy: float = Field(..., description="准确率")
    avg_cost: float = Field(..., description="平均成本")
    avg_response_time: float = Field(..., description="平均响应时间")


class StandardResponse(BaseModel):
    """标准响应格式"""
    code: int = Field(default=200, description="响应码")
    message: str = Field(default="success", description="响应消息")
    data: Optional[Dict] = Field(default=None, description="响应数据")
