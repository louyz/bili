from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func, desc, text
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from app.database import get_db
from app.models.video import Video
from app.models.video_tag import VideoTag
from app.models.up_user import UpUser
from app.schemas.video import VideoListItem, VideoDetail, VideoListResponse, UpUserInfo

router = APIRouter(prefix="/api/videos", tags=["视频"])


@router.get("/ranking", response_model=VideoListResponse)
async def get_video_ranking(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort_by: str = Query("heat_score", description="排序字段: heat_score, play_count, pub_time"),
    partition: Optional[str] = Query(None, description="分区筛选"),
    keyword: Optional[str] = Query(None, description="标题搜索关键词"),
    db: AsyncSession = Depends(get_db),
):
    base_query = select(Video).where(Video.is_active == True)

    if partition and partition != "全部":
        base_query = base_query.where(Video.partition_main == partition)
    if keyword:
        base_query = base_query.where(Video.title.contains(keyword))

    count_query = select(func.count()).select_from(base_query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    sort_col = getattr(Video, sort_by, Video.heat_score)
    query = base_query.order_by(desc(sort_col)).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    videos = result.scalars().all()

    items = []
    for v in videos:
        up_result = await db.execute(select(UpUser).where(UpUser.id == v.up_id))
        up = up_result.scalar_one_or_none()

        tag_result = await db.execute(
            select(VideoTag.tag_name).where(VideoTag.bvid == v.bvid)
        )
        tags = [row[0] for row in tag_result.all()]

        items.append(VideoListItem(
            id=v.id,
            bvid=v.bvid,
            title=v.title,
            cover_url=v.cover_url,
            play_count=v.play_count or 0,
            danmaku_count=v.danmaku_count or 0,
            comment_count=v.comment_count or 0,
            like_count=v.like_count or 0,
            coin_count=v.coin_count or 0,
            favorite_count=v.favorite_count or 0,
            share_count=v.share_count or 0,
            duration=v.duration or 0,
            pub_time=v.pub_time,
            partition_main=v.partition_main,
            partition_sub=v.partition_sub,
            interaction_rate=v.interaction_rate,
            heat_score=v.heat_score,
            up_nickname=up.nickname if up else None,
            up_follower_count=up.follower_count if up else None,
            tags=tags if tags else None,
            crawl_time=v.crawl_time,
        ))

    return VideoListResponse(total=total, page=page, page_size=page_size, items=items)


@router.get("/detail/{bvid}", response_model=VideoDetail)
async def get_video_detail(bvid: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Video).where(Video.bvid == bvid, Video.is_active == True))
    video = result.scalar_one_or_none()
    if not video:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="视频不存在")

    up_result = await db.execute(select(UpUser).where(UpUser.id == video.up_id))
    up = up_result.scalar_one_or_none()

    tag_result = await db.execute(select(VideoTag.tag_name).where(VideoTag.bvid == video.bvid))
    tags = [row[0] for row in tag_result.all()]

    return VideoDetail(
        id=video.id,
        bvid=video.bvid,
        title=video.title,
        cover_url=video.cover_url,
        description=video.description,
        play_count=video.play_count or 0,
        danmaku_count=video.danmaku_count or 0,
        comment_count=video.comment_count or 0,
        like_count=video.like_count or 0,
        coin_count=video.coin_count or 0,
        favorite_count=video.favorite_count or 0,
        share_count=video.share_count or 0,
        duration=video.duration or 0,
        pub_time=video.pub_time,
        partition_main=video.partition_main,
        partition_sub=video.partition_sub,
        interaction_rate=video.interaction_rate,
        heat_score=video.heat_score,
        up_user=UpUserInfo.model_validate(up) if up else None,
        tags=tags if tags else None,
        crawl_time=video.crawl_time,
    )


@router.get("/partitions")
async def get_partitions(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Video.partition_main, func.count(Video.id))
        .where(Video.is_active == True)
        .group_by(Video.partition_main)
        .order_by(desc(func.count(Video.id)))
    )
    return [{"name": row[0], "count": row[1]} for row in result.all()]