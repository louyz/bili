import asyncio
import random
from datetime import datetime

import httpx
from sqlalchemy import select
from app.config import settings
from app.database import AsyncSessionLocal
from app.models.video import Video
from app.models.up_user import UpUser
from app.models.video_tag import VideoTag
from app.models.crawl_log import CrawlLog, CrawlLogDetail
from app.services.test_playwright import fetch_data
from app.services.bilibili_client import (
    _safe_call,
    fetch_popular_list,
    fetch_video_tags,
)

_crawl_running = False
_crawl_stop_requested = False
_crawl_status = {"running": False, "message": "空闲中", "progress": "0/0"}


def get_crawl_status() -> dict:
    return _crawl_status


def stop_crawl_task():
    global _crawl_stop_requested
    _crawl_stop_requested = True
    _crawl_status["message"] = "正在停止..."


async def _random_delay(min_sec: float = None, max_sec: float = None):
    min_sec = min_sec if min_sec is not None else settings.CRAWL_DELAY_MIN
    max_sec = max_sec if max_sec is not None else settings.CRAWL_DELAY_MAX
    delay = random.uniform(min_sec, max_sec)
    await asyncio.sleep(delay)


async def start_crawl_task(task_type: str = "full_sync"):
    global _crawl_running, _crawl_status, _crawl_stop_requested
    if _crawl_running:
        _crawl_status["message"] = "已有爬虫任务在运行中"
        return
    _crawl_running = True
    _crawl_stop_requested = False
    _crawl_status = {"running": True, "message": "正在采集热门列表...", "progress": "0/0"}

    log_id = None
    async with AsyncSessionLocal() as db:
        log = CrawlLog(
            task_type=task_type,
            status="running",
            trigger_type="manual",
            started_at=datetime.now(),
        )
        db.add(log)
        await db.flush()
        log_id = log.id

        try:
            popular_videos = await _fetch_popular_list(log_id)
            total = len(popular_videos)
            log.total_videos = total
            _crawl_status["progress"] = f"0/{total}"

            success = 0
            failed = 0
            skipped = 0

            for idx, item in enumerate(popular_videos):
                try:
                    bvid = item.get("bvid", "")
                    title = item.get("title", "")
                    owner = item.get("owner", {})
                    stat = item.get("stat", {})
                    print(f"[{idx + 1}/{total}] {bvid} | {title} | UP主: {owner.get('name', '?')} | 播放: {stat.get('view', 0)} | 弹幕: {stat.get('danmaku', 0)}")

                    if _crawl_stop_requested:
                        _crawl_status["message"] = "已手动停止"
                        break

                    if not bvid:
                        skipped += 1
                        continue

                    await _process_video(item, db, log_id)
                    await db.commit()
                    success += 1
                    _crawl_status["progress"] = f"{idx + 1}/{total}"

                except Exception as e:
                    failed += 1
                    print(f"[爬虫] 处理视频失败 bvid={item.get('bvid')}: {e}")
                    detail = CrawlLogDetail(
                        log_id=log_id,
                        bvid=item.get("bvid", "unknown"),
                        api_step=0,
                        status="failed",
                        error_msg=str(e)[:1000],
                    )
                    db.add(detail)

            log.status = "success" if failed == 0 else "partial"
            log.success_count = success
            log.failed_count = failed
            log.skipped_count = skipped
            log.finished_at = datetime.now()
            if log.started_at:
                log.duration_ms = int((log.finished_at - log.started_at).total_seconds() * 1000)
            await db.commit()

            _crawl_status = {
                "running": False,
                "message": f"采集完成: 成功{success}, 失败{failed}, 跳过{skipped}",
                "progress": f"{success + failed + skipped}/{total}",
            }

        except Exception as e:
            import traceback
            traceback.print_exc()
            log.status = "failed"
            log.error_msg = str(e)[:5000]
            log.finished_at = datetime.now()
            await db.commit()
            _crawl_status = {"running": False, "message": f"采集失败: {str(e)[:100]}", "progress": "0/0"}

        finally:
            _crawl_running = False
            _crawl_stop_requested = False


async def _fetch_popular_list(log_id: int) -> list:
    all_videos = []
    for pn in range(1, settings.CRAWL_POPULAR_PAGES + 1):
        if _crawl_stop_requested:
            break

        async def _call(client):
            return await fetch_popular_list(client, pn=pn, ps=50)

        result = await _safe_call(
            _call,
            log_id=log_id,
            api_step=1,
            api_url=f"热门列表 pn={pn}",
        )
        if result is not None:
            videos = result.get("list", [])
            all_videos.extend(videos)
    return all_videos

# 测试爬虫
async def test_crawler():
    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
        for pn in range(1, settings.CRAWL_POPULAR_PAGES + 1):
            result = await fetch_popular_list(client, pn=pn, ps=50)
            videos = result.get("data",{}).get("list",[]) if result else []
            print(f"获取到 {len(videos)} 个视频")
            async with AsyncSessionLocal() as db:
                for video in videos:
                    await _process_video(video, db, log_id=0)
                    await _create_video_tags(client, db, video.get("bvid", ""))
                await db.commit()


# step 1 处理视频列表数据
async def _process_video(
    item: dict,
    db,
    log_id: int = 0,
):
    bvid = item.get("bvid", "")
    stat = item.get("stat", {})
    owner = item.get("owner", {})
    mid = owner.get("mid", 0)

    if mid == 0:
        return

    up_user = await _create_default_up(mid, db, owner)

    play = stat.get("view", 0)
    like = stat.get("like", 0)
    comment = stat.get("reply", 0)
    danmaku = stat.get("danmaku", 0)
    coin = stat.get("coin", 0)
    fav = stat.get("favorite", 0)
    share = stat.get("share", 0)
    pub_location = item.get("pub_location", "")
    partition_sub = item.get("tnamev2", "")
    total_interact = like + comment + danmaku + coin + fav + share
    interaction_rate = round(total_interact / play, 6) if play > 0 else 0

    heat_score = (
        play * 0.3 + like * 0.15 + comment * 0.15
        + danmaku * 0.1 + coin * 0.1 + fav * 0.1 + share * 0.1
    )

    pub_time = datetime.fromtimestamp(item.get("pubdate", 0))

    existing_video = (await db.execute(select(Video).where(Video.bvid == bvid))).scalar_one_or_none()

    if existing_video:
        existing_video.title = item.get("title", "")
        existing_video.cover_url = item.get("pic", "")
        existing_video.description = item.get("desc", "")
        existing_video.play_count = play
        existing_video.danmaku_count = danmaku
        existing_video.comment_count = comment
        existing_video.like_count = like
        existing_video.coin_count = coin
        existing_video.favorite_count = fav
        existing_video.share_count = share
        existing_video.duration = item.get("duration", 0)
        existing_video.pub_time = pub_time
        existing_video.pub_location = pub_location
        existing_video.partition_sub = partition_sub
        existing_video.partition_main = item.get("tname", "未知")
        existing_video.up_id = up_user.id
        existing_video.up_uid = mid
        existing_video.interaction_rate = interaction_rate
        existing_video.heat_score = round(heat_score, 2)
        existing_video.crawl_time = datetime.now()
        video = existing_video
        await db.flush()
    else:
        video = Video(
            bvid=bvid,
            title=item.get("title", ""),
            cover_url=item.get("pic", ""),
            description=item.get("desc", ""),
            play_count=play,
            danmaku_count=danmaku,
            comment_count=comment,
            like_count=like,
            coin_count=coin,
            favorite_count=fav,
            share_count=share,
            duration=item.get("duration", 0),
            pub_time=pub_time,
            pub_location=pub_location,
            partition_sub=partition_sub,
            partition_main=item.get("tname", "未知"),
            up_id=up_user.id,
            up_uid=mid,
            interaction_rate=interaction_rate,
            heat_score=round(heat_score, 2),
            crawl_time=datetime.now(),
        )
        db.add(video)
        await db.flush()
        await db.refresh(video)


# 创建UP主信息
async def _create_default_up(mid, db, owner) -> UpUser:
    if mid == 0:
        return None
    existing = (await db.execute(
        select(UpUser).where(UpUser.up_uid == mid)
    )).scalar_one_or_none()

    page_data = await fetch_data(mid)
    stats = page_data.get("data", {}) if page_data else {}

    def _parse_int(val):
        try:
            return int(val)
        except (TypeError, ValueError):
            return 0

    follower = _parse_int(stats.get("粉丝数"))
    following = _parse_int(stats.get("关注数"))
    total_likes = _parse_int(stats.get("获赞数"))
    total_plays = _parse_int(stats.get("播放数"))
    video_count = _parse_int(stats.get("视频"))
    image_text_count = _parse_int(stats.get("图文"))
    audio_count = _parse_int(stats.get("音频"))
    elec= _parse_int(stats.get("elec"))
    level= _parse_int(stats.get("level"))
    total=video_count+image_text_count+audio_count
    sign = stats.get("sign", "")
    if existing:
        existing.nickname = owner.get('name', '') or existing.nickname
        existing.avatar_url = owner.get('face', '') or existing.avatar_url
        existing.follower_count = follower or existing.follower_count
        existing.following_count = following or existing.following_count
        existing.total_likes = total_likes or existing.total_likes
        existing.total_plays = total_plays or existing.total_plays
        existing.video_count = video_count or existing.video_count
        existing.image_text_count = image_text_count or existing.image_text_count
        existing.audio_count = audio_count or existing.audio_count
        existing.level= level or existing.level
        existing.elec = elec or existing.elec
        existing.total = total or existing.total
        existing.sign = sign or existing.sign
        existing.crawl_time = datetime.now()
        await db.flush()
        return existing

    up = UpUser(
        up_uid=mid,
        nickname=owner.get('name', ''),
        avatar_url=owner.get('face', ''),
        follower_count=follower,
        following_count=following,
        total_likes=total_likes,
        total_plays=total_plays,
        video_count=video_count,
        image_text_count=image_text_count,
        audio_count=audio_count,
        total=total,
        elec=elec,
        level=level,
        sign=sign,
        crawl_time=datetime.now(),
    )
    db.add(up)
    await db.flush()
    await db.refresh(up)
    return up

# 创建视频标签并更新标签
async def _create_video_tags(client: httpx.AsyncClient, db, bvid: str):
    await asyncio.sleep(random.uniform(2, 5))
    result = await fetch_video_tags(client, bvid)
    if result is None:
        return
    tags = result.get("data", []) if result else []

    old_tags = (await db.execute(
        select(VideoTag).where(VideoTag.bvid == bvid)
    )).scalars().all()
    for t in old_tags:
        await db.delete(t)
    await db.flush()

    for tag in tags:
        video_tag = VideoTag(
            bvid=bvid,
            tag_id=tag.get("tag_id", 0),
            tag_name=tag.get("tag_name", ""),
            crawl_time=datetime.now(),
        )
        db.add(video_tag)
    await db.flush()