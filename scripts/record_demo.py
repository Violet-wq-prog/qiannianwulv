# -*- coding: utf-8 -*-
"""演示视频录制：Playwright 驱动真实运行的 app，完整走通业务全链路 + 年轻化玩法。

产出：
  submission/screenshots/*.png  原型截图（PPT / 开发日志佐证）
  submission/_video_raw/        Playwright 原始 webm
  submission/demo.mp4           ffmpeg 转码后的演示视频

前置：streamlit run app.py 已在本机运行（默认 http://localhost:8501）
运行：python scripts/record_demo.py
"""
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from imageio_ffmpeg import get_ffmpeg_exe
from playwright.sync_api import sync_playwright

from config import PROJECT_ROOT

BASE = "http://localhost:8501"
SUB = PROJECT_ROOT / "submission"
SHOT_DIR = SUB / "screenshots"
VIDEO_DIR = SUB / "_video_raw"
SAMPLE_SELFIE = SUB / "_sample_selfie.png"

SHOT_DELAY = 4.0   # 每张截图前的停顿（秒），让画面稳定可读、配音节奏从容


def _make_sample_selfie():
    """生成一张演示用"自拍"占位图（600×600）。"""
    if SAMPLE_SELFIE.exists():
        return
    from PIL import Image, ImageDraw
    img = Image.new("RGB", (600, 600), (222, 208, 182))
    d = ImageDraw.Draw(img)
    d.ellipse((200, 120, 400, 330), fill=(214, 178, 138))          # 脸
    d.polygon([(300, 250), (272, 300), (328, 300)], fill=(110, 82, 60))  # 发
    d.ellipse((300, 330, 600, 700), fill=(96, 122, 133))           # 身
    d.rectangle((0, 540, 600, 600), fill=(150, 132, 102))
    img.save(SAMPLE_SELFIE, "JPEG", quality=88)


def _shot(page, name: str):
    page.wait_for_timeout(int(SHOT_DELAY * 1000))
    page.screenshot(path=str(SHOT_DIR / f"{name}.png"))
    print("  截图:", name)


def _wait_msgs(page, n: int, timeout: int = 180000):
    page.wait_for_function(
        "n => document.querySelectorAll('[data-testid=\"stChatMessage\"]').length >= n",
        arg=n, timeout=timeout)


def _chat(page, text: str):
    box = page.locator('textarea[data-testid="stChatInputTextArea"]').first
    box.wait_for(state="visible", timeout=30000)
    box.fill(text)
    box.press("Enter")


def _pick_option(page, text: str):
    """baseweb 下拉选项（multiselect/selectbox 通用）。"""
    page.locator('li[role="option"], div[role="option"]', has_text=text).first.click()


def main():
    SUB.mkdir(parents=True, exist_ok=True)
    _make_sample_selfie()
    SHOT_DIR.mkdir(parents=True, exist_ok=True)
    VIDEO_DIR.mkdir(parents=True, exist_ok=True)
    for old in VIDEO_DIR.glob("*.webm"):  # 清掉上一次的残片，保证取到最新完整录像
        old.unlink()

    print("== 千年晤旅 演示视频录制 ==")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(
            viewport={"width": 1440, "height": 900},
            record_video_dir=str(VIDEO_DIR),
            record_video_size={"width": 1440, "height": 900},
        )
        page = ctx.new_page()
        page.goto(BASE)
        page.wait_for_timeout(5000)  # 等 Streamlit 首帧
        _shot(page, "01_home")

        # —— 入口A 文旅链路 ——
        page.get_by_role("button", name="开启一场人文游历").click()
        page.wait_for_timeout(1800)
        _shot(page, "02_explore")
        inp = page.get_by_placeholder("例：杭州 / 西湖 / 长安 / 黄州 / 南阳")
        inp.fill("杭州")
        inp.press("Enter")   # Streamlit 文本输入需回车提交
        page.wait_for_timeout(1200)
        page.get_by_role("button", name="检索此地故人").click()
        page.wait_for_timeout(2200)
        _shot(page, "03_explore_result")
        page.get_by_role("button", name="✨ 选TA同行").first.click()
        page.wait_for_timeout(1800)
        # 偏好：美食市井 + 慢游少赶路，2 天（天数现为 st.pills 选择），模式B（默认）
        page.locator('[data-testid="stMultiSelect"]').first.click()
        page.wait_for_timeout(600)
        _pick_option(page, "美食市井")
        _pick_option(page, "慢游少赶路")
        page.keyboard.press("Escape")
        page.get_by_text("2 天", exact=True).first.click()
        page.wait_for_timeout(800)
        _shot(page, "04_preference")
        page.get_by_role("button", name="🧭 生成成套游历路线").click()
        print("  等待 AI 生成路线……")
        page.locator('button:has-text("查看完整路线地图")').wait_for(timeout=240000)
        page.wait_for_timeout(2000)
        _shot(page, "05_route_gen")
        page.get_by_role("button", name="🗺️ 查看完整路线地图").click()
        page.wait_for_timeout(2200)
        _shot(page, "06_route_view")
        # 实景交互地图页（tab 切换，站点点击直达对话；1.61 tabs 为 role=tab）
        try:
            page.get_by_role("tab", name="实景地图").click()
            page.wait_for_timeout(3000)
            _shot(page, "06b_interactive_map")
            page.get_by_role("tab", name="画卷地图").click()
            page.wait_for_timeout(1000)
        except Exception:  # noqa: BLE001 —— 交互地图渲染失败不影响主流程
            pass

        # —— 逐站点故地重游 + 解锁（"下一站"在对话页内跳转，不回路线总览） ——
        n_sites = len(page.locator('button:has-text("前往对话")').all()) \
            + len(page.locator('button:has-text("再访对话")').all())
        print(f"  路线共 {n_sites} 站，逐站对话解锁")
        for i in range(n_sites):
            if i == 0:
                page.get_by_role("button", name="前往对话").first.click()
            else:
                page.get_by_role("button", name="下一站 →").click()
            page.wait_for_timeout(2500)
            msgs_before = page.locator('[data-testid="stChatMessage"]').count()
            if i == 0:
                _shot(page, "07_site_dialogue")
            _chat(page, "你当时是什么心情？")
            _wait_msgs(page, msgs_before + 2, timeout=180000)
            _chat(page, "后来呢？还有什么难忘的？")
            _wait_msgs(page, msgs_before + 4, timeout=180000)
            page.wait_for_timeout(800)
            page.get_by_role("button", name="✅ 完成对话 · 解锁打卡").click()
            page.wait_for_timeout(1800)
            if i == 0:
                _shot(page, "08_unlock")
        # 全站解锁 → 去合影
        page.get_by_role("button", name="📸 去同游合影").click()
        page.wait_for_timeout(1800)
        page.locator('input[type="file"]').set_input_files(str(SAMPLE_SELFIE))
        page.wait_for_timeout(800)
        page.get_by_role("button", name="🖼 生成同游合影").click()
        page.wait_for_timeout(5000)
        _shot(page, "09_photo")
        # 随笔 + 票根
        page.get_by_role("button", name="📝 写游历随笔").click()
        page.wait_for_timeout(1500)
        jbox = page.locator('textarea[aria-label="游历感悟"]')
        jbox.fill("站在苏堤上，忽然懂了什么叫'欲把西湖比西子'。谢谢苏先生带我看他守护过的杭州。")
        jbox.press("Tab")
        page.wait_for_timeout(800)
        page.get_by_role("button", name="🎫 生成时空票根").click()
        page.wait_for_timeout(3000)
        _shot(page, "10_ticket")
        page.get_by_role("button", name="💾 保存随笔").click()
        page.wait_for_timeout(1500)
        page.get_by_role("button", name="🏮 完成旅程 · 收入档案").click()
        page.wait_for_timeout(2500)
        _shot(page, "11_archive")

        # —— 入口B 单人对话 + 藏头诗 ——
        page.get_by_role("button", name="💬 单人闲谈").click()
        page.wait_for_timeout(1500)
        _shot(page, "12_solo_chat")          # 含语音输入按钮（浏览器 Web Speech）
        # Streamlit 1.61 的 selectbox 已迁移为 react-aria ComboBox：Open 按钮 + [role=option]
        page.locator('button[aria-label="Open"]').first.click()
        page.wait_for_timeout(900)
        page.locator('[role="option"]', has_text="李白").first.click()
        page.wait_for_timeout(2200)
        page.get_by_text("🎁 请李白为你写一首藏头诗", exact=False).click()
        page.wait_for_timeout(800)
        pn = page.get_by_label("你的名字（嵌入诗中）")
        pn.fill("小明")
        pn.press("Tab")
        msgs_before = page.locator('[data-testid="stChatMessage"]').count()
        page.get_by_role("button", name="求诗").click()
        _wait_msgs(page, msgs_before + 1, timeout=180000)
        page.wait_for_timeout(1500)
        _shot(page, "12_solo_poem")

        # —— 跨时代群聊（默认候选已是李白×苏轼，直接开聊） ——
        page.get_by_role("button", name="🎭 跨时代群聊").click()
        page.wait_for_timeout(1500)
        msgs_before = page.locator('[data-testid="stChatMessage"]').count()  # 点击前计数
        page.get_by_role("button", name="🎬 开启群聊").click()
        # 开场：离线剧本 1 条 / AI 模式全员同时到齐（≥1 即可）
        _wait_msgs(page, msgs_before + 1, timeout=300000)
        page.wait_for_timeout(1800)
        _chat(page, "两位聊聊月亮吧")
        # 游客 1 条 + 至少 1 位古人回应（离线 1 条 / AI 全员 2 条，≥3 即可）
        _wait_msgs(page, msgs_before + 3, timeout=300000)
        page.wait_for_timeout(1200)
        _shot(page, "13_group")

        # —— 古今人格测试 ——
        page.get_by_role("button", name="🎯 古今人格测试").click()
        page.wait_for_timeout(1200)
        for label in ["去古迹遗址，看历史留下的痕迹", "苦中作乐，把烂牌打出新花样",
                      "写点什么：诗、文章、歌词", "对月小酌/听歌emo，思绪飘到天外",
                      "幽默自嘲，再丧也能讲成段子", "老友常在，酒局诗会不断"]:
            page.get_by_text(label, exact=False).first.click()
            page.wait_for_timeout(500)
        _shot(page, "14_test_answers")
        page.get_by_role("button", name="🔮 揭晓我的古代人格").click()
        page.wait_for_timeout(3000)
        _shot(page, "15_test_result")

        # 结束：回首页定格
        page.get_by_role("button", name="🏠 首页").click()
        page.wait_for_timeout(3000)

        ctx.close()
        browser.close()
    print("录制完成，开始转码 mp4……")

    webms = sorted(VIDEO_DIR.glob("*.webm"))
    if not webms:
        print("!! 未找到 webm 录像")
        return
    out = SUB / "demo.mp4"
    subprocess.run([
        get_ffmpeg_exe(), "-y", "-i", str(webms[-1]),
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "23",
        "-movflags", "+faststart", str(out),
    ], check=True, capture_output=True)
    size_mb = out.stat().st_size / 1024 / 1024
    print(f"演示视频: {out} ({size_mb:.1f} MB)")


if __name__ == "__main__":
    main()
