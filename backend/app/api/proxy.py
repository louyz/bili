from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
import httpx
from urllib.parse import unquote

router = APIRouter(prefix="/api/proxy", tags=["图片代理"])


@router.get("/image")
async def proxy_image(url: str = Query(..., description="原始图片URL")):
    url = unquote(url)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://www.bilibili.com/",
    }
    try:
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            resp = await client.get(url, headers=headers)
            if resp.status_code != 200:
                raise HTTPException(status_code=404, detail="图片获取失败")
            content_type = resp.headers.get("content-type", "image/jpeg")
            return StreamingResponse(
                content=iter([resp.content]),
                media_type=content_type,
                headers={"Cache-Control": "public, max-age=86400"},
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))