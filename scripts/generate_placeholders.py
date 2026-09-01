# -*- coding: utf-8 -*-
"""一次性脚本：程序化生成国风水墨剪影占位立绘与古风背景。

占位图说明：替换为真实国风写实立绘时，直接覆盖 assets/characters/{person_id}.png
（透明底、人物居中、建议 512x768），代码零改动。
运行：python scripts/generate_placeholders.py
"""
import sys
import zlib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from PIL import Image, ImageDraw, ImageFilter

from config import BG_DIR, CHAR_DIR
from core.photo_utils import find_cn_font
from data.people import PEOPLE

SIZE = (512, 768)
INK = (43, 40, 36)
SEAL = (192, 57, 43)


def _rng(seed: str) -> int:
    return zlib.crc32(seed.encode("utf-8"))


def draw_character(person: dict, out: Path):
    """水墨剪影 + 印章 + 竖排名讳。"""
    img = Image.new("RGBA", SIZE, (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    seed = _rng(person["id"])

    # 1. 墨晕背景（多层半透明圆模拟毛笔晕染）
    halo = Image.new("RGBA", SIZE, (0, 0, 0, 0))
    hd = ImageDraw.Draw(halo)
    cx, cy = 256 + (seed % 40) - 20, 330
    for i in range(7):
        r = 260 - i * 28
        alpha = 10 + i * 2
        hd.ellipse((cx - r, cy - r * 1.1, cx + r, cy + r * 1.1),
                   fill=(43, 40, 36, alpha))
    halo = halo.filter(ImageFilter.GaussianBlur(12))
    img.alpha_composite(halo)

    # 2. 剪影人像：发髻 + 头 + 肩身衣摆
    jx = (seed % 25) - 12
    d.ellipse((cx - 70 + jx, 120, cx + 70 + jx, 260), fill=(*INK, 235))       # 头
    d.ellipse((cx - 42 + jx, 68, cx + 42 + jx, 152), fill=(*INK, 235))       # 发髻
    d.polygon([(cx - 135, 280 + (seed % 14)), (cx + 135, 280),
               (cx + 195, 768), (cx - 195, 768)], fill=(*INK, 228))          # 肩身
    d.polygon([(cx - 150, 290), (cx + 150, 290), (cx + 175, 768),
               (cx - 175, 768)], fill=(*INK, 120))                           # 外袍层次
    d.line((cx - 30, 285, cx + 20, 340), fill=(247, 241, 227, 90), width=14) # 衣领
    d.line((cx - 150, 540 + (seed % 30), cx + 150, 540), fill=(247, 241, 227, 70), width=6)

    # 3. 底部红印：姓氏
    seal_text = person["name"][0]
    try:
        font_seal = find_cn_font(88)
        d.rounded_rectangle((cx - 70, 620, cx + 70, 748), radius=14, fill=(*SEAL, 245),
                            outline=(255, 255, 255, 150), width=4)
        bbox = d.textbbox((0, 0), seal_text, font=font_seal)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        d.text((cx - tw / 2, 620 + (128 - th) / 2 - 12), seal_text,
               font=font_seal, fill=(255, 250, 240, 255))
    except FileNotFoundError:
        pass

    # 4. 右侧竖排名讳
    try:
        font_name = find_cn_font(40)
        x = 448
        for k, ch in enumerate(person["name"]):
            d.text((x + 4, 300 + k * 52 + 4), ch, font=font_name, fill=(*INK, 60))
            d.text((x, 300 + k * 52), ch, font=font_name, fill=(*INK, 215))
    except FileNotFoundError:
        pass

    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out, "PNG")


def draw_background(out: Path, seed: int):
    """1280x800 宣纸米底 + 水墨远山 + 淡月。"""
    W, H = 1280, 800
    img = Image.new("RGB", (W, H), (247, 241, 227))
    d = ImageDraw.Draw(img)
    for y in range(H):
        t = y / H
        d.line([(0, y), (W, y)], fill=(
            int(250 - 12 * t), int(244 - 12 * t), int(231 - 12 * t)), width=1)

    # 淡月
    mx, my = 150 + (seed % 180), 130
    moon = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    md = ImageDraw.Draw(moon)
    md.ellipse((mx - 46, my - 46, mx + 46, my + 46), fill=(192, 57, 43, 42))
    moon = moon.filter(ImageFilter.GaussianBlur(6))
    img.paste(Image.new("RGB", (W, H), (247, 241, 227)), (0, 0))
    img = Image.alpha_composite(img.convert("RGBA"), moon).convert("RGB")

    # 三层远山（crc 抖动）
    r = _rng(f"bg{seed}")
    for layer, (base_y, alpha, shift) in enumerate([(520, 60, 160), (600, 85, 90), (680, 105, 220)]):
        pts = [(0, base_y + 80)]
        for i in range(0, W + 80, 80):
            y = base_y - ((zlib.crc32(f"{r}{layer}{i}".encode()) % 3) * 26) \
                - (zlib.crc32(f"m{layer}{i}".encode()) % 40)
            pts.append((i, y))
        pts += [(W, base_y + 80), (0, base_y + 80)]
        d.polygon(pts, fill=(58, 50, 38, alpha))

    # 底部雾带
    mist = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    mm = ImageDraw.Draw(mist)
    for i in range(3):
        mm.ellipse((-(i * 220), 700 - i * 40, W + (i * 220), 900), fill=(247, 241, 227, 60))
    mist = mist.filter(ImageFilter.GaussianBlur(30))
    img = Image.alpha_composite(img.convert("RGBA"), mist).convert("RGB")
    img.save(out, "PNG")


if __name__ == "__main__":
    CHAR_DIR.mkdir(parents=True, exist_ok=True)
    BG_DIR.mkdir(parents=True, exist_ok=True)
    for p in PEOPLE:
        draw_character(p, CHAR_DIR / f"{p['id']}.png")
        print(f"立绘：{p['name']} -> {CHAR_DIR / f'{p['id']}.png'}")
    for i in range(2):
        draw_background(BG_DIR / f"bg_ink_{i + 1}.png", seed=i * 7 + 3)
        print(f"背景：bg_ink_{i + 1}.png")
    # 清空立绘缓存：若 Streamlit 进程内已加载旧图，避免合成继续用旧立绘
    from core.photo_utils import _load_character
    _load_character.cache_clear()
    print("完成。占位图可由真实国风美术资源同名替换（512x768 透明底，见 portrait_prompts.md）。")
