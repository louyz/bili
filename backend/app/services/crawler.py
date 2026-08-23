import asyncio
import time
from datetime import datetime
from typing import Optional
import httpx
from sqlalchemy import select
from app.config import settings
from app.database import AsyncSessionLocal
from app.models.video import Video
from app.models.video_tag import VideoTag
from app.models.up_user import UpUser
from app.models.snapshot import VideoSnapshot, UpUserSnapshot
from app.models.crawl_log import CrawlLog, CrawlLogDetail

_crawl_running = False
_crawl_status = {"running": False, "message": "空闲中", "progress": "0/0"}

BILI_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Referer": "https://www.bilibili.com/",
}


def get_crawl_status() -> dict:
    return _crawl_status


async def start_crawl_task(task_type: str = "full_sync"):
    global _crawl_running, _crawl_status
    if _crawl_running:
        _crawl_status["message"] = "已有爬虫任务在运行中"
        return
    _crawl_running = True
    _crawl_status = {"running": True, "message": "正在采集...", "progress": "0/0"}

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
            async with httpx.AsyncClient(timeout=30.0, headers=BILI_HEADERS) as client:
                popular_videos = await _fetch_popular_list(client, log_id)
                total = len(popular_videos)
                log.total_videos = total
                _crawl_status["progress"] = f"0/{total}"

                success = 0
                failed = 0
                skipped = 0

                for idx, item in enumerate(popular_videos):
                    try:
                        bvid = item.get("bvid", "")
                        if not bvid:
                            skipped += 1
                            continue

                        existing = await db.execute(
                            select(Video).where(Video.bvid == bvid)
                        )
                        if existing.scalar_one_or_none():
                            skipped += 1
                            _crawl_status["progress"] = f"{idx + 1}/{total}"
                            continue

                        await _process_video(client, item, db, log_id)
                        await db.commit()
                        success += 1
                        _crawl_status["progress"] = f"{idx + 1}/{total}"

                    except Exception as e:
                        failed += 1
                        detail = CrawlLogDetail(
                            log_id=log_id,
                            bvid=item.get("bvid", "unknown"),
                            api_step=0,
                            status="failed",
                            error_msg=str(e)[:1000],
                        )
                        db.add(detail)

                    await asyncio.sleep(settings.CRAWL_REQUEST_DELAY)

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
                    "progress": f"{total}/{total}",
                }

        except Exception as e:
            log.status = "failed"
            log.error_msg = str(e)[:5000]
            log.finished_at = datetime.now()
            await db.commit()
            _crawl_status = {"running": False, "message": f"采集失败: {str(e)[:100]}", "progress": "0/0"}

        finally:
            _crawl_running = False


async def _fetch_popular_list(client: httpx.AsyncClient, log_id: int) -> list:
    all_videos = []
    for pn in range(1, settings.CRAWL_POPULAR_PAGES + 1):
        url = f"https://api.bilibili.com/x/web-interface/popular?pn={pn}&ps=50"
        for retry in range(settings.CRAWL_MAX_RETRY):
            try:
                resp = await client.get(url)
                data = resp.json()
                if data.get("code") == 0:
                    videos = data.get("data", {}).get("list", [])
                    all_videos.extend(videos)
                    break
                else:
                    if retry == settings.CRAWL_MAX_RETRY - 1:
                        async with AsyncSessionLocal() as db:
                            detail = CrawlLogDetail(
                                log_id=log_id, bvid="", api_step=1,
                                api_url=url, status="failed",
                                http_status=resp.status_code,
                                error_msg=f"API返回错误: {data.get('message', '')}"[:1000],
                                retry_count=retry + 1,
                            )
                            db.add(detail)
                            await db.flush()
            except Exception as e:
                if retry == settings.CRAWL_MAX_RETRY - 1:
                    async with AsyncSessionLocal() as db:
                        detail = CrawlLogDetail(
                            log_id=log_id, bvid="", api_step=1,
                            api_url=url, status="failed",
                            error_msg=str(e)[:1000],
                            retry_count=retry + 1,
                        )
                        db.add(detail)
                        await db.flush()
            await asyncio.sleep(1)
        await asyncio.sleep(settings.CRAWL_REQUEST_DELAY)
    return all_videos


async def _process_video(client: httpx.AsyncClient, item: dict, db, log_id: int):
    bvid = item.get("bvid", "")
    stat = item.get("stat", {})
    owner = item.get("owner", {})
    mid = owner.get("mid", 0)

    # Step 1: 处理UP主信息
    up_user = await _get_or_create_up_user(client, mid, db, log_id)

    # Step 2: 获取视频标签
    tags = await _fetch_video_tags(client, bvid, log_id)

    # Step 3: 计算衍生字段
    play = stat.get("view", 0)
    like = stat.get("like", 0)
    comment = stat.get("reply", 0)
    danmaku = stat.get("danmaku", 0)
    coin = stat.get("coin", 0)
    fav = stat.get("favorite", 0)
    share = stat.get("share", 0)

    total_interact = like + comment + danmaku + coin + fav + share
    interaction_rate = round(total_interact / play, 6) if play > 0 else 0

    heat_score = (
        play * 0.3 + like * 0.15 + comment * 0.15
        + danmaku * 0.1 + coin * 0.1 + fav * 0.1 + share * 0.1
    )

    pub_time = datetime.fromtimestamp(item.get("pubdate", 0))

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
        partition_main=item.get("tname", "未知"),
        up_id=up_user.id,
        up_uid=mid,
        interaction_rate=interaction_rate,
        heat_score=round(heat_score, 2),
        crawl_time=datetime.now(),
    )
    db.add(video)
    await db.flush()

    # 写入标签
    for tag_name in tags:
        vt = VideoTag(bvid=bvid, tag_name=tag_name, crawl_time=datetime.now())
        db.add(vt)

    # 写入视频快照
    snapshot = VideoSnapshot(
        bvid=bvid,
        video_id=video.id,
        up_id=up_user.id,
        play_count=play,
        danmaku_count=danmaku,
        comment_count=comment,
        like_count=like,
        coin_count=coin,
        favorite_count=fav,
        share_count=share,
        interaction_rate=interaction_rate,
        heat_score=round(heat_score, 2),
        snapshot_date=datetime.now().date(),
        crawl_time=datetime.now(),
    )
    db.add(snapshot)

    # 写入UP主快照
    up_snapshot = UpUserSnapshot(
        up_id=up_user.id,
        up_uid=mid,
        follower_count=up_user.follower_count,
        following_count=up_user.following_count,
        total_likes=up_user.total_likes,
        total_plays=up_user.total_plays,
        video_count=up_user.video_count,
        snapshot_date=datetime.now().date(),
        crawl_time=datetime.now(),
    )
    db.add(up_snapshot)


async def _get_or_create_up_user(client: httpx.AsyncClient, mid: int, db, log_id: int) -> UpUser:
    if mid == 0:
        return await _create_default_up(db)

    result = await db.execute(select(UpUser).where(UpUser.up_uid == mid))
    existing = result.scalar_one_or_none()
    if existing:
        return existing

    nickname = "未知"
    sex = "保密"
    level = 0
    sign = ""
    avatar = ""
    follower = 0
    following = 0
    total_likes = 0
    total_plays = 0
    video_count = 0

    # Step ③: UP主信息
    try:
        resp = await client.get(f"https://api.bilibili.com/x/space/acc/info?mid={mid}")
        data = resp.json()
        if data.get("code") == 0:
            d = data.get("data", {})
            nickname = d.get("name", "未知")
            sex = d.get("sex", "保密")
            level = d.get("level", 0)
            sign = d.get("sign", "")
            avatar = d.get("face", "")
    except Exception:
        pass

    # Step ④: UP主统计 (粉丝/关注)
    try:
        resp = await client.get(f"https://api.bilibili.com/x/relation/stat?vmid={mid}")
        data = resp.json()
        if data.get("code") == 0:
            d = data.get("data", {})
            follower = d.get("follower", 0)
            following = d.get("following", 0)
    except Exception:
        pass

    # Step ⑤: UP主投稿统计
    try:
        resp = await client.get(f"https://api.bilibili.com/x/space/upstat?mid={mid}")
        data = resp.json()
        if data.get("code") == 0:
            d = data.get("data", {})
            total_likes = d.get("likes", 0)
            total_plays = d.get("archive", {}).get("view", 0)
    except Exception:
        pass

    # Step ⑥: UP主视频总数
    try:
        resp = await client.get(f"https://api.bilibili.com/x/space/arc/search?mid={mid}&pn=1&ps=50")
        data = resp.json()
        if data.get("code") == 0:
            video_count = data.get("data", {}).get("page", {}).get("count", 0)
    except Exception:
        pass

    up_user = UpUser(
        up_uid=mid,
        nickname=nickname,
        sex=sex,
        level=level,
        sign=sign,
        avatar_url=avatar,
        follower_count=follower,
        following_count=following,
        total_likes=total_likes,
        total_plays=total_plays,
        video_count=video_count,
        crawl_time=datetime.now(),
    )
    db.add(up_user)
    await db.flush()
    await db.refresh(up_user)
    return up_user


async def _create_default_up(db) -> UpUser:
    result = await db.execute(select(UpUser).where(UpUser.up_uid == 0))
    existing = result.scalar_one_or_none()
    if existing:
        return existing
    up = UpUser(
        up_uid=0,
        nickname="未知UP主",
        crawl_time=datetime.now(),
    )
    db.add(up)
    await db.flush()
    await db.refresh(up)
    return up


async def _fetch_video_tags(client: httpx.AsyncClient, bvid: str, log_id: int) -> list:
    url = f"https://api.bilibili.com/x/web-interface/view/detail?bvid={bvid}"
    for retry in range(settings.CRAWL_MAX_RETRY):
        try:
            resp = await client.get(url)
            data = resp.json()
            if data.get("code") == 0:
                tags_data = data.get("data", {}).get("Tags", [])
                return [t.get("tag_name", "") for t in tags_data if t.get("tag_name")]
            else:
                if retry == settings.CRAWL_MAX_RETRY - 1:
                    async with AsyncSessionLocal() as db2:
                        detail = CrawlLogDetail(
                            log_id=log_id, bvid=bvid, api_step=2,
                            api_url=url, status="failed",
                            http_status=resp.status_code,
                            error_msg=f"API错误: {data.get('message', '')}"[:1000],
                            retry_count=retry + 1,
                        )
                        db2.add(detail)
                        await db2.flush()
        except Exception as e:
            if retry == settings.CRAWL_MAX_RETRY - 1:
                async with AsyncSessionLocal() as db2:
                    detail = CrawlLogDetail(
                        log_id=log_id, bvid=bvid, api_step=2,
                        api_url=url, status="failed",
                        error_msg=str(e)[:1000],
                        retry_count=retry + 1,
                    )
                    db2.add(detail)
                    await db2.flush()
        await asyncio.sleep(1)
    return []