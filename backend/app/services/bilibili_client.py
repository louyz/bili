"""
B站 API 客户端 —— 基于 httpx 原生 HTTP 请求 + WBI 签名

改造要点:
- 放弃 bilibili-api-python，改用 httpx 直接发请求
- 浏览器级别请求头伪装，降低 -799 风控概率
- 手动实现 WBI 签名（w_rid / wts）
- 指数退避重试，-799 自动等待更长时间
"""
import asyncio
import hashlib
import random
import sys
import time
import urllib.parse
from typing import Optional

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import httpx

from app.config import settings
from app.database import AsyncSessionLocal
from app.models.crawl_log import CrawlLogDetail

# ---------------------------------------------------------------------------
# 浏览器伪装请求头
# ---------------------------------------------------------------------------
_BASE_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/128.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Origin": "https://www.bilibili.com",
    "Referer": "https://www.bilibili.com/",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-site",
    "Connection": "keep-alive",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
}

# ---------------------------------------------------------------------------
# WBI 签名缓存
# ---------------------------------------------------------------------------
_wbi_keys: Optional[tuple] = None
_wbi_keys_ts: float = 0
_WBI_CACHE_TTL: float = 3600.0  # 1小时刷新一次


def _build_cookie_string() -> str:
    """用配置中的凭证构建 Cookie 字符串"""
    parts = []
    if settings.BILI_SESSDATA:
        parts.append(f"SESSDATA={settings.BILI_SESSDATA}")
    if settings.BILI_BUVID3:
        parts.append(f"buvid3={settings.BILI_BUVID3}")
    if settings.BILI_BILI_JCT:
        parts.append(f"bili_jct={settings.BILI_BILI_JCT}")
    if settings.BILI_DEDEUSERID:
        parts.append(f"DedeUserID={settings.BILI_DEDEUSERID}")
    if settings.BILI_BUVID4:
        parts.append(f"buvid4={settings.BILI_BUVID4}")
    if getattr(settings, "BILI_BUVID_FP", ""):
        parts.append(f"buvid_fp={settings.BILI_BUVID_FP}")
    if getattr(settings, "BILI_B_NUT", ""):
        parts.append(f"b_nut={settings.BILI_B_NUT}")
    if getattr(settings, "BILI_UUID", ""):
        parts.append(f"_uuid={settings.BILI_UUID}")
    if getattr(settings, "BILI_BILI_TICKET", ""):
        parts.append(f"bili_ticket={settings.BILI_BILI_TICKET}")
    if getattr(settings, "BILI_BILI_TICKET_EXPIRES", ""):
        parts.append(f"bili_ticket_expires={settings.BILI_BILI_TICKET_EXPIRES}")
    if getattr(settings, "BILI_SID", ""):
        parts.append(f"sid={settings.BILI_SID}")
    if getattr(settings, "BILI_B_LSID", ""):
        parts.append(f"b_lsid={settings.BILI_B_LSID}")
    return "; ".join(parts)


_COOKIE_STRING: Optional[str] = None


def _get_cookie() -> str:
    global _COOKIE_STRING
    if _COOKIE_STRING is None:
        _COOKIE_STRING = _build_cookie_string()
    return _COOKIE_STRING


# ---------------------------------------------------------------------------
# WBI 签名
# ---------------------------------------------------------------------------

_MIXIN_KEY_ENC_TAB = [
    46, 47, 18, 2, 53, 8, 23, 32, 15, 50, 10, 31, 58, 3, 45, 35,
    27, 43, 5, 49, 33, 9, 42, 19, 29, 28, 14, 39, 12, 38, 41, 13,
    37, 48, 7, 16, 24, 55, 40, 61, 26, 17, 0, 1, 60, 51, 30, 4,
    22, 25, 54, 21, 56, 59, 6, 63, 57, 62, 11, 36, 20, 52, 44, 34,
]


def _get_mixin_key(orig: str) -> str:
    return "".join(orig[n] for n in _MIXIN_KEY_ENC_TAB if n < len(orig))[:32]


async def _fetch_wbi_keys(client: httpx.AsyncClient) -> tuple:
    global _wbi_keys, _wbi_keys_ts
    now = time.time()
    if _wbi_keys and (now - _wbi_keys_ts) < _WBI_CACHE_TTL:
        return _wbi_keys

    headers = {**_BASE_HEADERS}
    resp = await client.get(
        "https://api.bilibili.com/x/web-interface/nav",
        headers=headers,
    )
    data = resp.json().get("data", {})
    wbi_img = data.get("wbi_img", {})
    img_key = wbi_img.get("img_url", "").rsplit("/", 1)[-1].split(".")[0]
    sub_key = wbi_img.get("sub_url", "").rsplit("/", 1)[-1].split(".")[0]
    _wbi_keys = (img_key, sub_key)
    _wbi_keys_ts = now
    return _wbi_keys


def _sign_params(params: dict, img_key: str, sub_key: str) -> dict:
    mixin_key = _get_mixin_key(img_key + sub_key)
    params["wts"] = int(time.time())
    params = dict(sorted(params.items()))
    query = urllib.parse.urlencode(params)
    params["w_rid"] = hashlib.md5((query + mixin_key).encode()).hexdigest()
    return params


# ---------------------------------------------------------------------------
# HTTP 请求工具
# ---------------------------------------------------------------------------

async def _random_delay(min_sec: float = None, max_sec: float = None):
    min_sec = min_sec if min_sec is not None else settings.CRAWL_DELAY_MIN
    max_sec = max_sec if max_sec is not None else settings.CRAWL_DELAY_MAX
    delay = random.uniform(min_sec, max_sec)
    await asyncio.sleep(delay)


async def _api_get(
    client: httpx.AsyncClient,
    url: str,
    params: dict = None,
    need_wbi: bool = False,
) -> dict:
    headers = {**_BASE_HEADERS}
    cookie = _get_cookie()
    if cookie:
        headers["Cookie"] = cookie

    params = dict(params or {})
    if need_wbi:
        img_key, sub_key = await _fetch_wbi_keys(client)
        params = _sign_params(params, img_key, sub_key)

    resp = await client.get(url, params=params, headers=headers)
    return resp.json()


async def _safe_call(
    api_func,
    log_id: int,
    api_step: int,
    bvid: str = "",
    api_url: str = "",
    max_retry: int = None,
):
    max_retry = max_retry if max_retry is not None else settings.CRAWL_MAX_RETRY
    last_error = None

    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
        for retry in range(max_retry):
            await _random_delay()

            try:
                result = await api_func(client)
                code = result.get("code", 0)
                msg = result.get("message", "")

                if code == 0:
                    return result.get("data")

                if code == -799:
                    backoff = settings.CRAWL_RATE_LIMIT_BACKOFF * (2 ** retry)
                    print(f"[风控-799] 等待 {backoff:.0f}s 后重试 (第{retry + 1}/{max_retry}次)...")
                    await asyncio.sleep(backoff)
                    continue

                if code == -412:
                    backoff = settings.CRAWL_RATE_LIMIT_BACKOFF
                    print(f"[被拦截-412] 等待 {backoff:.0f}s 后重试...")
                    await asyncio.sleep(backoff)
                    continue

                if retry == max_retry - 1:
                    async with AsyncSessionLocal() as db:
                        detail = CrawlLogDetail(
                            log_id=log_id, bvid=bvid, api_step=api_step,
                            api_url=api_url, status="failed",
                            error_msg=f"code={code} msg={msg}"[:1000],
                            retry_count=retry + 1,
                        )
                        db.add(detail)
                        await db.flush()
                last_error = Exception(f"API code={code} msg={msg}")

            except (httpx.TimeoutException, httpx.NetworkError) as e:
                last_error = e
                if retry == max_retry - 1:
                    async with AsyncSessionLocal() as db:
                        detail = CrawlLogDetail(
                            log_id=log_id, bvid=bvid, api_step=api_step,
                            api_url=api_url, status="failed",
                            error_msg=str(e)[:1000],
                            retry_count=retry + 1,
                        )
                        db.add(detail)
                        await db.flush()

            except Exception as e:
                last_error = e
                if retry == max_retry - 1:
                    async with AsyncSessionLocal() as db:
                        detail = CrawlLogDetail(
                            log_id=log_id, bvid=bvid, api_step=api_step,
                            api_url=api_url, status="failed",
                            error_msg=str(e)[:1000],
                            retry_count=retry + 1,
                        )
                        db.add(detail)
                        await db.flush()

    if last_error:
        raise last_error
    return None


# ---------------------------------------------------------------------------
# 业务 API 封装
# ---------------------------------------------------------------------------

async def fetch_popular_list(client: httpx.AsyncClient, pn: int, ps: int = 50) -> dict:
    return await _api_get(
        client,
        "https://api.bilibili.com/x/web-interface/popular",
        params={"pn": pn, "ps": ps},
        need_wbi=False,
    )

# 获取视频标签
async def fetch_video_tags(client: httpx.AsyncClient, bvid: str) -> dict:
    return await _api_get(
        client,
        "https://api.bilibili.com/x/tag/archive/tags",
        params={"bvid": bvid},
        need_wbi=False,
    )


async def fetch_video_detail(client: httpx.AsyncClient, bvid: str) -> dict:
    return await _api_get(
        client,
        "https://api.bilibili.com/x/web-interface/view",
        params={"bvid": bvid},
        need_wbi=False,
    )

# 获取up主信息
async def fetch_user_info(client: httpx.AsyncClient, mid: int) -> dict:
    return await _api_get(
        client,
        "https://api.bilibili.com/x/space/wbi/acc/info",
        params={"mid": mid},
        need_wbi=True,
    )


async def fetch_user_relation(client: httpx.AsyncClient, mid: int) -> dict:
    return await _api_get(
        client,
        "https://api.bilibili.com/x/relation/stat",
        params={"vmid": mid},
        need_wbi=False,
    )


async def fetch_user_upstat(client: httpx.AsyncClient, mid: int) -> dict:
    return await _api_get(
        client,
        "https://api.bilibili.com/x/space/upstat",
        params={"mid": mid},
        need_wbi=False,
    )


async def fetch_user_videos(client: httpx.AsyncClient, mid: int, pn: int = 1, ps: int = 50) -> dict:
    return await _api_get(
        client,
        "https://api.bilibili.com/x/space/wbi/arc/search",
        params={"mid": mid, "pn": pn, "ps": ps},
        need_wbi=True,
    )