from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
import asyncio
import traceback
from app.database import get_db
from app.models.user import User
from app.models.crawl_log import CrawlLog
from app.utils.security import get_current_admin, hash_password
from app.schemas.user import UserCreateByAdmin, UserEditByAdmin, UserResetPassword
from app.services.crawler import start_crawl_task, get_crawl_status, stop_crawl_task, test_crawler
from app.services.test_playwright import fetch_data
router = APIRouter(prefix="/api/admin", tags=["管理后台"])

# 测试爬虫
@router.get("/testCrawler")
async def testCrawler(
    page: int = Query(1, ge=1),):
    await test_crawler()
    return {"message": "测试完成"}

# 页面数据测试
@router.get("/upPage/{mid}")
async def get_up_page(
    mid: int,
):
    page = await fetch_data(mid)
    if not page:
        raise HTTPException(status_code=500, detail="获取UP主空间页失败")
    return {"page": page}

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


@router.post("/users")
async def create_user(
    req: UserCreateByAdmin,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    existing = await db.execute(
        select(User).where((User.username == req.username) | (User.email == req.email))
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="用户名或邮箱已存在")
    user = User(
        username=req.username,
        email=req.email,
        password_hash=hash_password(req.password),
        nickname=req.nickname,
        role="user",
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "nickname": user.nickname,
        "role": user.role,
        "is_active": user.is_active,
        "created_at": str(user.created_at),
    }


@router.put("/users/{user_id}")
async def update_user(
    user_id: int,
    req: UserEditByAdmin,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    if req.email is not None and req.email != user.email:
        dup = await db.execute(select(User).where(User.email == req.email, User.id != user_id))
        if dup.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="邮箱已被其他用户使用")
        user.email = req.email
    if req.nickname is not None:
        user.nickname = req.nickname
    if req.is_active is not None:
        if user.role == "admin" and not req.is_active:
            raise HTTPException(status_code=400, detail="不能禁用管理员账号")
        if user.id == current_user.id and not req.is_active:
            raise HTTPException(status_code=400, detail="不能禁用自己的账号")
        user.is_active = req.is_active
    await db.flush()
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "nickname": user.nickname,
        "role": user.role,
        "is_active": user.is_active,
        "created_at": str(user.created_at),
    }


@router.put("/users/{user_id}/reset-password")
async def reset_user_password(
    user_id: int,
    req: UserResetPassword,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    user.password_hash = hash_password(req.new_password)
    await db.flush()
    return {"message": "密码已重置"}


async def _run_crawl_safe(task_type: str):
    try:
        await start_crawl_task(task_type=task_type)
    except Exception as e:
        traceback.print_exc()
        print(f"[爬虫] 后台任务异常: {e}")


@router.post("/crawl/trigger")
async def trigger_crawl(
    task_type: str = Query("full_sync", description="任务类型: full_sync, popular"),
    current_user: User = Depends(get_current_admin),
):
    status = get_crawl_status()
    if status.get("running"):
        return {"message": "已有爬虫任务在运行中，请等待完成或停止后再触发"}
    asyncio.create_task(_run_crawl_safe(task_type=task_type))
    return {"message": f"爬虫任务已触发，类型: {task_type}"}


@router.post("/crawl/stop")
async def stop_crawl(
    current_user: User = Depends(get_current_admin),
):
    stop_crawl_task()
    return {"message": "爬虫停止指令已发送"}


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