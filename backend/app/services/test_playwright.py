import asyncio
import json
import subprocess
import sys
import urllib.parse


def _build_cookies_from_env():
    try:
        from app.config import settings
    except Exception:
        return []

    cookie_map = {
        "SESSDATA": settings.BILI_SESSDATA,
        "buvid3": settings.BILI_BUVID3,
        "bili_jct": settings.BILI_BILI_JCT,
        "DedeUserID": settings.BILI_DEDEUSERID,
        "buvid4": settings.BILI_BUVID4,
        "buvid_fp": getattr(settings, "BILI_BUVID_FP", ""),
        "b_nut": getattr(settings, "BILI_B_NUT", ""),
        "_uuid": getattr(settings, "BILI_UUID", ""),
        "bili_ticket": getattr(settings, "BILI_BILI_TICKET", ""),
        "bili_ticket_expires": getattr(settings, "BILI_BILI_TICKET_EXPIRES", ""),
        "sid": getattr(settings, "BILI_SID", ""),
        "b_lsid": getattr(settings, "BILI_B_LSID", ""),
    }
    cookies = []
    for name, value in cookie_map.items():
        if value:
            cookies.append({
                "name": name,
                "value": urllib.parse.unquote(value),
                "domain": ".bilibili.com",
                "path": "/",
            })
    return cookies


async def fetch_data(mid: int):
    result = await asyncio.to_thread(
        subprocess.run,
        [sys.executable, "-u", __file__, str(mid)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=120,
    )
    if result.stdout:
        for line in result.stdout.splitlines():
            stripped = line.strip()
            if stripped and not stripped.startswith("{") and not stripped.startswith("["):
                print(f"[子进程] {stripped}")
    if result.stderr:
        print(f"[子进程 stderr] {result.stderr}")
    if result.returncode != 0:
        print(f"[子进程] 退出码 {result.returncode}")
        return None
    try:
        return json.loads(result.stdout.splitlines()[-1])
    except json.JSONDecodeError:
        print(f"[子进程] 输出非 JSON: {result.stdout}")
        return None


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

    mid = sys.argv[1] if len(sys.argv) > 1 else "17138783"
    print(f"[参数] mid={mid}", flush=True)

    from playwright.async_api import async_playwright

    async def _inner(mid: int):
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/128.0.0.0 Safari/537.36"
                ),
                viewport={"width": 1920, "height": 1080},
                locale="zh-CN",
            )

            cookies = _build_cookies_from_env()
            if cookies:
                await context.add_cookies(cookies)
                print(f"[Cookie] 已注入 {len(cookies)} 个 Cookie", flush=True)
            else:
                print("[Cookie] 未配置 Cookie，将以游客身份访问", flush=True)

            page = await context.new_page()
            print("[步骤] 正在访问页面...", flush=True)
            await page.goto(f'https://space.bilibili.com/{mid}', wait_until="networkidle")
            title = await page.title()
            print(f'标题是title: {title}', flush=True)

            print("[步骤] 等待 nav-statistics 元素...", flush=True)
            try:
                await page.wait_for_selector('div.nav-statistics', state="attached", timeout=15000)
                print("[步骤] nav-statistics 已出现", flush=True)
            except Exception as e:
                print(f"[步骤] nav-statistics 未出现: {e}", flush=True)

            print("[步骤] 开始执行 divs_info evaluate...", flush=True)
            divs_info = await page.evaluate("""() => {
                try {
                    const navStats = document.querySelector('div.nav-statistics');
                    if (!navStats) {
                        return {error: 'nav-statistics 未找到'};
                    }
                    const items = Array.from(navStats.querySelectorAll('.nav-statistics__item'));
                    const result = {};
                    items.forEach(item => {
                        const textEl = item.querySelector('.nav-statistics__item-text');
                        const numEl = item.querySelector('.nav-statistics__item-num');
                        if (!textEl || !numEl) return;
                        const label = textEl.textContent.trim();
                        const displayValue = numEl.textContent.trim();
                        let titleValue = numEl.getAttribute('title') || displayValue;
                        titleValue = titleValue.replace(/[\u4e00-\u9fa5，。、；：！？]/g, '').replace(/^[^\d]*,/, '').trim();
                        const match = titleValue.match(/[\d,]+/);
                        titleValue = match ? match[0].replace(/,/g, '') : titleValue;
                        result[label] = titleValue;
                    });
                    const elecStatus = document.querySelector('div.elec-status__count strong');
                    if (elecStatus) {
                        result['elec'] = elecStatus.textContent.trim();
                    }
                    const levelIcon = document.querySelector('.level-icon');
                    if (levelIcon) {
                        const cls = levelIcon.className;
                        const match = cls.match(/level_(\d+)/);
                        if (match) {
                            result['level'] = parseInt(match[1]);
                        }
                    }
                    const signEl = document.querySelector('.header-sign .pure-text');
                    if (signEl) {
                        result['sign'] = signEl.getAttribute('title') || signEl.textContent.trim();
                    }
                    return result;
                } catch (e) {
                    return {error: e.message};
                }
            }""")
            print(f"[divs_info] {divs_info}", flush=True)

            print("[步骤] 准备点击第3个a标签...", flush=True)
            third_link = page.locator('div.nav-bar__main-left .nav-tab a').nth(2)
            link_text = await third_link.text_content()
            print(f'[点击] 第3个a标签: {link_text}', flush=True)
            await third_link.click()
            await page.wait_for_load_state("networkidle")
            new_title = await page.title()
            print(f'[点击后] 标题: {new_title}, URL: {page.url}', flush=True)

            print("[步骤] 等待 side-nav 元素...", flush=True)
            try:
                await page.wait_for_selector('.side-nav', state="attached", timeout=10000)
                print('[等待] .side-nav 已出现', flush=True)
            except Exception as e:
                print(f'[等待] .side-nav 未出现: {e}', flush=True)

            print("[步骤] 开始执行 texts evaluate...", flush=True)
            texts = await page.evaluate("""() => {
                const container = document.querySelector('div.side-nav');
                if (!container) {
                    return null;
                }
                const items = Array.from(container.querySelectorAll('.side-nav__item'));
                const result = {};
                items.forEach(item => {
                    const textEl = item.querySelector('.side-nav__item__main-text');
                    const numEl = item.querySelector('.side-nav__item__sub-text');
                    if (!textEl || !numEl) return;
                    const label = textEl.textContent.trim();
                    const num = numEl.textContent.trim();
                    result[label] = num;
                });
                return result;
            }""")
            print(f"[side-nav] {texts}", flush=True)

            await context.close()
            await browser.close()
            print("[步骤] 浏览器已关闭", flush=True)
        merged = {}
        if divs_info:
            merged.update(divs_info)
        if texts:
            merged.update(texts)
        return {
            "title": title,
            "mid": mid,
            "data": merged,
        }

    try:
        data = asyncio.run(_inner(int(mid)))
        print(json.dumps(data, ensure_ascii=False))
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(json.dumps({"error": str(e)}, ensure_ascii=False))