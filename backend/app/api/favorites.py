from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from app.database import get_db
from app.models.user import User
from app.models.video import Video
from app.models.favorite import Favorite, FavoriteFolder
from app.utils.security import get_current_user

router = APIRouter(prefix="/api/favorites", tags=["收藏"])


@router.get("/folders")
async def get_folders(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(FavoriteFolder)
        .where(FavoriteFolder.user_id == current_user.id)
        .order_by(FavoriteFolder.sort_order)
    )
    folders = result.scalars().all()
    return [
        {
            "id": f.id,
            "name": f.name,
            "description": f.description,
            "is_public": f.is_public,
            "video_count": f.video_count,
            "created_at": str(f.created_at),
        }
        for f in folders
    ]


@router.post("/folders")
async def create_folder(
    name: str = Query(..., min_length=1, max_length=100),
    description: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    folder = FavoriteFolder(
        user_id=current_user.id,
        name=name,
        description=description,
    )
    db.add(folder)
    await db.flush()
    await db.refresh(folder)
    return {"id": folder.id, "name": folder.name, "message": "创建成功"}


@router.delete("/folders/{folder_id}")
async def delete_folder(
    folder_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(FavoriteFolder).where(
            FavoriteFolder.id == folder_id,
            FavoriteFolder.user_id == current_user.id,
        )
    )
    folder = result.scalar_one_or_none()
    if not folder:
        raise HTTPException(status_code=404, detail="收藏夹不存在")
    await db.delete(folder)
    await db.execute(
        select(Favorite).where(Favorite.folder_id == folder_id)
    )
    return {"message": "删除成功"}


@router.get("/videos")
async def get_favorite_videos(
    folder_id: Optional[int] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    base_query = select(Favorite).where(Favorite.user_id == current_user.id)
    if folder_id is not None:
        base_query = base_query.where(Favorite.folder_id == folder_id)

    count_query = select(func.count()).select_from(base_query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    result = await db.execute(
        base_query.order_by(desc(Favorite.created_at))
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    favs = result.scalars().all()

    items = []
    for fav in favs:
        video_result = await db.execute(select(Video).where(Video.id == fav.video_id))
        video = video_result.scalar_one_or_none()
        if video:
            items.append({
                "id": fav.id,
                "video_id": video.id,
                "bvid": video.bvid,
                "title": video.title,
                "cover_url": video.cover_url,
                "play_count": video.play_count,
                "heat_score": video.heat_score,
                "note": fav.note,
                "created_at": str(fav.created_at),
            })

    return {"total": total, "page": page, "page_size": page_size, "items": items}


@router.post("/videos/{bvid}")
async def add_favorite(
    bvid: str,
    folder_id: Optional[int] = Query(None),
    note: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    video_result = await db.execute(select(Video).where(Video.bvid == bvid))
    video = video_result.scalar_one_or_none()
    if not video:
        raise HTTPException(status_code=404, detail="视频不存在")

    exist_result = await db.execute(
        select(Favorite).where(
            Favorite.user_id == current_user.id,
            Favorite.video_id == video.id,
            Favorite.folder_id == folder_id,
        )
    )
    if exist_result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="已收藏该视频")

    fav = Favorite(
        user_id=current_user.id,
        video_id=video.id,
        folder_id=folder_id,
        note=note,
    )
    db.add(fav)
    await db.flush()

    if folder_id:
        folder_result = await db.execute(
            select(FavoriteFolder).where(FavoriteFolder.id == folder_id)
        )
        folder = folder_result.scalar_one_or_none()
        if folder:
            folder.video_count = (folder.video_count or 0) + 1

    return {"message": "收藏成功", "id": fav.id}


@router.delete("/videos/{bvid}")
async def remove_favorite(
    bvid: str,
    folder_id: Optional[int] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    video_result = await db.execute(select(Video).where(Video.bvid == bvid))
    video = video_result.scalar_one_or_none()
    if not video:
        raise HTTPException(status_code=404, detail="视频不存在")

    fav_result = await db.execute(
        select(Favorite).where(
            Favorite.user_id == current_user.id,
            Favorite.video_id == video.id,
            Favorite.folder_id == folder_id,
        )
    )
    fav = fav_result.scalar_one_or_none()
    if not fav:
        raise HTTPException(status_code=404, detail="未收藏该视频")

    await db.delete(fav)
    if folder_id:
        folder_result = await db.execute(
            select(FavoriteFolder).where(FavoriteFolder.id == folder_id)
        )
        folder = folder_result.scalar_one_or_none()
        if folder and folder.video_count > 0:
            folder.video_count -= 1

    return {"message": "取消收藏成功"}