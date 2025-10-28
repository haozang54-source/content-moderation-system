"""API路由"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict
import uuid
from datetime import datetime

from api.schemas import (
    ReviewRequest,
    ReviewResponse,
    ReviewStatus,
    ReviewResult,
    BatchReviewRequest,
    StatsResponse,
    StandardResponse
)

router = APIRouter(prefix="/api/v1", tags=["审核"])

# 临时存储（实际应使用数据库）
tasks_storage: Dict[str, ReviewResponse] = {}


@router.post("/review", response_model=ReviewResponse, summary="提交审核任务")
async def submit_review(
    request: ReviewRequest,
    background_tasks: BackgroundTasks,
    sync: bool = False
) -> ReviewResponse:
    """提交内容审核任务
    
    Args:
        request: 审核请求
        background_tasks: 后台任务
        sync: 是否同步执行（用于测试）
        
    Returns:
        ReviewResponse: 审核响应
    """
    # 生成任务ID
    task_id = str(uuid.uuid4())
    
    if sync:
        # 同步执行审核（用于测试）
        from core.pipeline import ModerationPipeline, ContentData
        from config.settings import Settings
        
        settings = Settings()
        pipeline = ModerationPipeline(settings)
        
        content_data = ContentData(
            content_type=request.content_type,
            content=request.content,
            text=request.content if request.content_type == "text" else None
        )
        
        try:
            import asyncio
            result = await pipeline.execute(content_data)
            
            # 创建完成的响应
            response = ReviewResponse(
                task_id=task_id,
                status=ReviewStatus.COMPLETED,
                result=ReviewResult(
                    is_compliant=result.is_compliant,
                    confidence=result.confidence,
                    violation_types=result.violation_types,
                    suggestions=result.suggestions,
                    details=result.details
                ),
                completed_at=datetime.now()
            )
        except Exception as e:
            response = ReviewResponse(
                task_id=task_id,
                status=ReviewStatus.FAILED,
                error=str(e)
            )
    else:
        # 异步执行（正常模式）
        response = ReviewResponse(
            task_id=task_id,
            status=ReviewStatus.PENDING,
            estimated_time=5
        )
        # 添加后台任务（实际应使用Celery）
        # background_tasks.add_task(process_review, task_id, request)
    
    # 存储任务
    tasks_storage[task_id] = response
    
    return response


@router.get("/review/{task_id}", response_model=ReviewResponse, summary="查询审核结果")
async def get_review_result(task_id: str) -> ReviewResponse:
    """查询审核结果
    
    Args:
        task_id: 任务ID
        
    Returns:
        ReviewResponse: 审核响应
    """
    if task_id not in tasks_storage:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    return tasks_storage[task_id]


@router.post("/review/batch", summary="批量审核")
async def batch_review(request: BatchReviewRequest, sync: bool = False):
    """批量审核
    
    Args:
        request: 批量审核请求
        sync: 是否同步执行
        
    Returns:
        批量审核结果
    """
    if sync:
        # 同步执行（用于测试）
        from core.pipeline import ModerationPipeline, ContentData
        from config.settings import Settings
        
        settings = Settings()
        pipeline = ModerationPipeline(settings)
        
        results = []
        for item in request.items:
            content_data = ContentData(
                content_type=item.content_type,
                content=item.content,
                text=item.content if item.content_type == "text" else None
            )
            
            try:
                result = await pipeline.execute(content_data)
                results.append({
                    "is_compliant": result.is_compliant,
                    "confidence": result.confidence,
                    "violation_types": result.violation_types,
                    "suggestions": result.suggestions
                })
            except Exception as e:
                results.append({
                    "error": str(e)
                })
        
        return {"results": results}
    else:
        # 异步执行（正常模式）
        task_ids = []
        
        for item in request.items:
            task_id = str(uuid.uuid4())
            response = ReviewResponse(
                task_id=task_id,
                status=ReviewStatus.PENDING,
                estimated_time=5
            )
            tasks_storage[task_id] = response
            task_ids.append(task_id)
        
        return StandardResponse(
            code=200,
            message="批量任务已提交",
            data={"task_ids": task_ids, "callback_url": request.callback_url}
        )


@router.get("/stats", response_model=StatsResponse, summary="获取统计信息")
async def get_stats(
    start_date: str = "2024-01-01",
    end_date: str = "2024-12-31"
) -> StatsResponse:
    """获取统计信息
    
    Args:
        start_date: 开始日期
        end_date: 结束日期
        
    Returns:
        StatsResponse: 统计响应
    """
    # 临时返回模拟数据
    total = 100000
    rejected = 12000
    return StatsResponse(
        total_reviews=total,
        passed=85000,
        rejected=rejected,
        human_review=3000,
        accuracy=0.92,
        avg_cost=0.045,
        avg_response_time=4.2,
        violation_rate=rejected / total if total > 0 else 0
    )


@router.post("/admin/reload-rules", response_model=StandardResponse, summary="重载规则")
async def reload_rules() -> StandardResponse:
    """重载规则配置
    
    Returns:
        StandardResponse: 标准响应
    """
    # 实际应调用规则引擎的hot_reload方法
    return StandardResponse(
        code=200,
        message="规则已重载"
    )
