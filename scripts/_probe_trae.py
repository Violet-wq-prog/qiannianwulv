# -*- coding: utf-8 -*-
"""临时探针 v4：监听下载页 API 请求，找版本/下载地址接口（排障用）。"""
import io
from playwright.sync_api import sync_playwright

reqs = []


def on_request(req):
    u = req.url
    if any(k in u.lower() for k in ["api", "version", "download", "latest", "release", "installer", "upgrade"]):
        reqs.append(u)


with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    ctx = b.new_context(viewport={"width": 1440, "height": 900},
                        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36")
    pg = ctx.new_page()
    pg.on("request", on_request)
    pg.goto("https://www.trae.cn/download", timeout=60000, wait_until="domcontentloaded")
    pg.wait_for_timeout(8000)
    out = ["REQUESTS:"]
    out += reqs[:30]
    # 读取页面里可能存在的 window.__INITIAL_STATE__ 或 JSON
    try:
        state = pg.evaluate("() => JSON.stringify(window.__INITIAL_STATE__ || window.__NUXT__ || window.__APP__ || '')")
        out.append("STATE:" + state[:2000])
    except Exception as e:
        out.append("STATE_ERR: " + str(e)[:150])
    io.open("_trae_links.txt", "w", encoding="utf-8").write("\n".join(out))
    b.close()
