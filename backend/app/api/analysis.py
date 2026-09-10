from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func, desc, text
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta
from app.database import get_db
from app.models.video import Video
from app.models.video_tag import VideoTag
from app.models.up_user import UpUser
from app.schemas.video import DashboardStats, TrendDataPoint, PartitionStat, TagFrequencyItem

router = APIRouter(prefix="/api/analysis", tags=["数据分析"])


@router.get("/dashboard", response_model=DashboardStats)
async def get_dashboard(db: AsyncSession = Depends(get_db)):
    total_result = await db.execute(
        select(func.count(Video.id)).where(Video.is_active == True)
    )
    total_videos = total_result.scalar() or 0

    today = datetime.now().date()
    today_result = await db.execute(
        select(func.count(Video.id)).where(
            Video.is_active == True,
            func.date(Video.crawl_time) == today,
        )
    )
    today_new = today_result.scalar() or 0

    avg_result = await db.execute(
        select(func.avg(Video.play_count)).where(Video.is_active == True)
    )
    avg_play = avg_result.scalar() or 0

    up_result = await db.execute(
        select(func.count(func.distinct(Video.up_uid))).where(Video.is_active == True)
    )
    active_up = up_result.scalar() or 0

    return DashboardStats(
        total_videos=total_videos,
        today_new_videos=today_new,
        avg_play_count=round(float(avg_play), 0),
        active_up_count=active_up,
    )


@router.get("/trends", response_model=list[TrendDataPoint])
async def get_trends(
    days: int = Query(7, ge=1, le=90),
    db: AsyncSession = Depends(get_db),
):
    start_date = datetime.now().date() - timedelta(days=days)
    result = await db.execute(
        select(
            func.date(Video.crawl_time).label("snapshot_date"),
            func.avg(Video.play_count).label("avg_play"),
            func.count(Video.id).label("cnt"),
        )
        .where(Video.is_active == True, func.date(Video.crawl_time) >= start_date)
        .group_by(func.date(Video.crawl_time))
        .order_by(func.date(Video.crawl_time))
    )
    rows = result.all()
    return [
        TrendDataPoint(
            date=str(row[0]),
            avg_play_count=round(float(row[1] or 0), 0),
            video_count=row[2],
        )
        for row in rows
    ]


@router.get("/partitions", response_model=list[PartitionStat])
async def get_partition_stats(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(
            Video.partition_main,
            func.count(Video.id).label("cnt"),
            func.avg(Video.heat_score).label("avg_heat"),
        )
        .where(Video.is_active == True)
        .group_by(Video.partition_main)
        .order_by(desc(text("cnt")))
    )
    rows = result.all()
    return [
        PartitionStat(partition=row[0], count=row[1], avg_heat_score=round(float(row[2] or 0), 2))
        for row in rows
    ]


@router.get("/tags", response_model=list[TagFrequencyItem])
async def get_tag_frequency(
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    subq = (
        select(
            VideoTag.tag_name,
            func.count(func.distinct(VideoTag.bvid)).label("video_count"),
        )
        .group_by(VideoTag.tag_name)
        .subquery()
    )
    result = await db.execute(
        select(
            subq.c.tag_name,
            subq.c.video_count,
        )
        .order_by(desc(subq.c.video_count))
        .limit(limit)
    )
    rows = result.all()

    items = []
    for row in rows:
        avg_result = await db.execute(
            select(func.avg(Video.play_count), func.avg(Video.heat_score))
            .select_from(VideoTag)
            .join(Video, VideoTag.bvid == Video.bvid)
            .where(VideoTag.tag_name == row[0], Video.is_active == True)
        )
        stats = avg_result.one_or_none()
        items.append(TagFrequencyItem(
            tag_name=row[0],
            video_count=row[1],
            avg_play_count=round(float(stats[0] or 0), 0),
            avg_heat_score=round(float(stats[1] or 0), 2),
        ))
    return items


@router.get("/up-rank")
async def get_up_rank(
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(
            Video.up_uid,
            UpUser.nickname,
            func.count(Video.id).label("video_count"),
            func.avg(Video.play_count).label("avg_play"),
            func.avg(Video.heat_score).label("avg_heat"),
        )
        .outerjoin(UpUser, Video.up_uid == UpUser.up_uid)
        .where(Video.is_active == True)
        .group_by(Video.up_uid, UpUser.nickname)
        .order_by(desc(text("avg_heat")))
        .limit(limit)
    )
    rows = result.all()
    return [
        {
            "up_uid": row[0],
            "up_nickname": row[1] or "未知",
            "video_count": row[2],
            "avg_play_count": round(float(row[3] or 0), 0),
            "avg_heat_score": round(float(row[4] or 0), 2),
        }
        for row in rows
    ]


@router.get("/up-contribution")
async def get_up_contribution(
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    contribution = (
        func.coalesce(UpUser.video_count, 0)
        + func.coalesce(UpUser.audio_count, 0)
        + func.coalesce(UpUser.image_text_count, 0)
    ).label("contribution")

    result = await db.execute(
        select(
            UpUser.up_uid,
            UpUser.nickname,
            UpUser.avatar_url,
            UpUser.level,
            UpUser.video_count,
            UpUser.audio_count,
            UpUser.image_text_count,
            UpUser.elec,
            UpUser.follower_count,
            contribution,
        )
        .order_by(desc(contribution))
        .limit(limit)
    )
    rows = result.all()
    return [
        {
            "up_uid": row[0],
            "up_nickname": row[1] or "未知",
            "avatar_url": row[2],
            "level": row[3] or 0,
            "video_count": row[4] or 0,
            "audio_count": row[5] or 0,
            "image_text_count": row[6] or 0,
            "elec": row[7] or 0,
            "follower_count": row[8] or 0,
            "total_contribution": row[9] or 0,
        }
        for row in rows
    ]