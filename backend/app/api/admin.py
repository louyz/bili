from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from app.database import get_db
from app.models.user import User
from app.models.crawl_log import CrawlLog
from app.utils.security import get_current_admin
from app.services.crawler import start_crawl_task, get_crawl_status

router = APIRouter(prefix="/api/admin", tags=["管理后台"])


@router.get("/users")
async def get_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    count_result = await db.execute(select(func.count(User.id)))
    total = count_result.scalar() or 0

    result = await db.execute(
        select(User).order_by(User.id).offset((page - 1) * page_size).limit(page_size)
    )
    users = result.scalars().all()
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [
            {
                "id": u.id,
                "username": u.username,
                "email": u.email,
                "nickname": u.nickname,
                "role": u.role,
                "is_active": u.is_active,
                "created_at": str(u.created_at),
            }
            for u in users
        ],
    }


@router.put("/users/{user_id}/toggle-active")
async def toggle_user_active(
    user_id: int,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="不能禁用自己的账号")
    user.is_active = not user.is_active
    await db.flush()
    return {"message": "状态已更新", "is_active": user.is_active}


@router.post("/crawl/trigger")
async def trigger_crawl(
    background_tasks: BackgroundTasks,
    task_type: str = Query("full_sync", description="任务类型: full_sync, popular"),
    current_user: User = Depends(get_current_admin),
):
    background_tasks.add_task(start_crawl_task, task_type=task_type)
    return {"message": f"爬虫任务已触发，类型: {task_type}"}


@router.get("/crawl/status")
async def crawl_status(
    current_user: User = Depends(get_current_admin),
):
    return get_crawl_status()


@router.get("/crawl/logs")
async def get_crawl_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    count_result = await db.execute(select(func.count(CrawlLog.id)))
    total = count_result.scalar() or 0

    result = await db.execute(
        select(CrawlLog)
        .order_by(desc(CrawlLog.id))
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    logs = result.scalars().all()
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [
            {
                "id": log.id,
                "task_type": log.task_type,
                "status": log.status,
                "trigger_type": log.trigger_type,
                "total_videos": log.total_videos,
                "success_count": log.success_count,
                "failed_count": log.failed_count,
                "skipped_count": log.skipped_count,
                "error_msg": log.error_msg,
                "started_at": str(log.started_at) if log.started_at else None,
                "finished_at": str(log.finished_at) if log.finished_at else None,
                "duration_ms": log.duration_ms,
            }
            for log in logs
        ],
    }