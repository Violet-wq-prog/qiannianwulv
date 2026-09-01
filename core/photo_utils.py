# -*- coding: utf-8 -*-
"""合影合成：PIL 管线（古风背景 + 用户自拍 + 人物立绘 + 题跋印章）。

真实 AI 图像合成留待未来迭代；本模块保证离线也可产出"我与古人同游"合影。
"""
import functools
import io
import zlib
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

from config import BG_DIR, CHAR_DIR, FONTS_DIR, FONT_CANDIDATES

OUT_SIZE = (1280, 800)


@functools.lru_cache(maxsize=64)
def find_cn_font(size: int) -> ImageFont.FreeTypeFont:
    """Windows 下探测可用的中文字体（楷体优先，古风题跋更佳）。

    字体对象不可 pickle（无法进 st.cache_data），用进程级 lru_cache：
    一次合成内 3-5 次重复加载 5-15MB 字体文件的耗时归零。
    """
    for name in FONT_CANDIDATES:
        path = FONTS_DIR / name
        if path.exists():
            return ImageFont.truetype(str(path), size)
    raise FileNotFoundError("未找到中文字体（Windows/Fonts 下应有楷体或微软雅黑）")


@functools.lru_cache(maxsize=16)
def _ellipse_mask(size: tuple[int, int]) -> Image.Image:
    """椭圆软边蒙版（用于自拍裁成画中人）。"""
    mask = Image.new("L", size, 0)
    d = ImageDraw.Draw(mask)
    d.ellipse((2, 2, size[0] - 2, size[1] - 2), fill=255)
    return mask.filter(ImageFilter.GaussianBlur(6))


def _draw_seal(draw: ImageDraw.ImageDraw, x: int, y: int, text: str, size: int = 64):
    """红色印章装饰（圆角方印 + 白字）。"""
    w = size + 24
    draw.rounded_rectangle((x, y, x + w, y + w), radius=10, fill=(192, 57, 43, 255),
                           outline=(255, 255, 255, 160), width=3)
    font = find_cn_font(size)
    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text((x + (w - tw) / 2, y + (w - th) / 2 - size * 0.06), text,
              font=font, fill=(255, 250, 240, 255))


@functools.lru_cache(maxsize=64)
def _load_character(person_id: str) -> Image.Image | None:
    """加载人物立绘；缺失时程序化画一个简笔剪影兜底。

    缓存注意：替换/重新生成立绘后需 _load_character.cache_clear()（进程内），
    scripts/generate_placeholders.py 尾部已处理。
    """
    path = CHAR_DIR / f"{person_id}.png"
    if path.exists():
        img = Image.open(path).convert("RGBA")
        # 统一缩放到约 65% 高度
        h = int(OUT_SIZE[1] * 0.68)
        w = int(img.width * h / img.height)
        return img.resize((w, h), Image.LANCZOS)
    # 兜底剪影
    img = Image.new("RGBA", (512, 768), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.ellipse((156, 80, 356, 300), fill=(45, 42, 38, 235))          # 头
    d.polygon([(110, 360), (402, 360), (470, 768), (42, 768)], fill=(45, 42, 38, 235))  # 身
    h = int(OUT_SIZE[1] * 0.68)
    return img.resize((int(512 * h / 768), h), Image.LANCZOS)


@functools.lru_cache(maxsize=8)
def _load_background(seed: int = 0) -> Image.Image:
    """背景图按 seed 确定性选取（背景库共 2 张，seed 取自人物 id 的 crc32 % 97）。"""
    bgs = sorted(BG_DIR.glob("*.png"))
    if bgs:
        return Image.open(bgs[seed % len(bgs)]).convert("RGBA").resize(OUT_SIZE, Image.LANCZOS)
    img = Image.new("RGBA", OUT_SIZE, (247, 241, 227, 255))
    d = ImageDraw.Draw(img)
    for i in range(60):  # 简易宣纸渐变
        d.line([(0, i * 14), (OUT_SIZE[0], i * 14)], fill=(247 - i, 241 - i, 227 - i, 255), width=14)
    return img


def compose_photo(selfie_bytes: bytes, person: dict, place_name: str,
                  out_path: str | Path) -> Path:
    """合成合影并保存，返回输出路径。"""
    out_path = Path(out_path)
    base = _load_background(seed=zlib.crc32(person["id"].encode()) % 97).copy()

    # 1. 古人立绘（右侧）
    char = _load_character(person["id"])
    cx = OUT_SIZE[0] - char.width - 70
    cy = OUT_SIZE[1] - char.height
    base.alpha_composite(char, (cx, cy))

    # 2. 用户自拍（左侧，椭圆软边裁切）
    selfie = Image.open(io.BytesIO(selfie_bytes)).convert("RGBA")
    selfie.thumbnail((600, 600), Image.LANCZOS)
    mask = _ellipse_mask(selfie.size)
    sx, sy = 90, OUT_SIZE[1] - selfie.height - 20
    base.paste(selfie, (sx, sy), mask)
    # 自拍描边
    d = ImageDraw.Draw(base)
    d.ellipse((sx + 2, sy + 2, sx + selfie.width - 2, sy + selfie.height - 2),
              outline=(176, 141, 79, 220), width=4)

    # 3. 题跋 + 印章 + 画框
    title = f"我与{person['name']}同游{place_name}"
    try:
        font_title = find_cn_font(46)
        font_sub = find_cn_font(26)
        d.text((70, 46), title, font=font_title, fill=(58, 50, 38, 255))
        d.text((74, 112), f"—— {person['dynasty']}{person['category']} · 千年晤旅", font=font_sub,
               fill=(138, 124, 102, 255))
        _draw_seal(d, 70, 170, "千年晤旅", size=40)
    except FileNotFoundError:
        pass
    # 双线画框
    d.rectangle((12, 12, OUT_SIZE[0] - 12, OUT_SIZE[1] - 12), outline=(74, 59, 43, 255), width=5)
    d.rectangle((22, 22, OUT_SIZE[0] - 22, OUT_SIZE[1] - 22), outline=(176, 141, 79, 255), width=2)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    base.convert("RGB").save(out_path, "PNG")
    return out_path


def make_ticket(route: dict, person: dict, trip_id: int, created_at: str,
                out) -> Path | io.BytesIO:
    """时空票根：古风车票样式（撕口 + 主券/副券 + 印章），年轻化的收藏玩法。

    out 为路径时落盘并返回 Path；为 file-like（如 BytesIO）时直接写入（零临时文件）。
    """
    W, H = 620, 960
    img = Image.new("RGBA", (W, H), (250, 244, 231, 255))
    d = ImageDraw.Draw(img)
    for y in range(H):  # 宣纸渐变
        t = y / H
        d.line([(0, y), (W, y)], fill=(int(250 - 14 * t), int(244 - 16 * t), int(231 - 18 * t), 255), width=1)

    INK = (58, 50, 38)
    GOLD = (176, 141, 79)
    SEAL = (192, 57, 43)

    # 主券区
    f_brand = find_cn_font(30)
    f_title = find_cn_font(52)
    f_mid = find_cn_font(30)
    f_small = find_cn_font(24)
    d.text((44, 46), "🏮 千年晤旅 · 时空游历纪念票根", font=f_brand, fill=INK)
    d.line((40, 96, W - 40, 96), fill=GOLD, width=2)

    bbox = d.textbbox((0, 0), route["route_name"], font=f_title)
    d.text(((W - (bbox[2] - bbox[0])) / 2, 140), route["route_name"], font=f_title, fill=INK)

    rows = [
        ("游历地", route["city"]),
        ("同行古人", f"{person['name']} · {person['dynasty']}{person['category']}"),
        ("行程天数", f"{route['days']} 天 · {len(route['sites'])} 站"),
        ("路线模式", "人物视角优先" if route["mode"] == "person_lead" else "双向融合"),
        ("发券日期", created_at[:16]),
    ]
    y = 260
    for k, v in rows:
        d.text((60, y), k, font=f_mid, fill=(138, 124, 102, 255))
        d.text((220, y), v, font=f_mid, fill=INK)
        y += 58

    # 印章
    _draw_seal(d, 430, 500, "已游", size=56)
    # 副券分隔（点线）与撕口
    d.line((60, 640, W - 60, 640), fill=(138, 124, 102, 255), width=2)
    for i in range(60, W - 60, 24):
        d.line((i, 640, i + 12, 640), fill=(138, 124, 102, 255), width=2)
    # 两侧撕口（半圆，用页面底色覆盖）
    d.pieslice((-30, 600, 30, 680), 90, 270, fill=(250, 244, 231, 255))
    d.pieslice((W - 30, 600, W + 30, 680), -90, 90, fill=(250, 244, 231, 255))

    # 副券区
    d.text((60, 690), "存根 · NO." + f"{trip_id:04d}", font=f_mid, fill=INK)
    d.text((60, 750), f"{person['name']}伴游 · {route['city']}", font=f_small, fill=(138, 124, 102, 255))
    d.text((60, 800), "与古人同游故地，听亲历者讲往事", font=f_small, fill=(138, 124, 102, 255))
    # 伪二维码装饰（crc 确定性图案）
    qx, qy, qs = W - 190, 700, 130
    d.rectangle((qx, qy, qx + qs, qy + qs), fill=(250, 250, 245, 255), outline=INK, width=2)
    seed = zlib.crc32(f"{trip_id}{person['id']}".encode())
    cell = 10
    for i in range(cell):
        for j in range(cell):
            if zlib.crc32(f"{seed}{i}{j}".encode()) % 100 < 42:
                d.rectangle((qx + 4 + i * 12, qy + 4 + j * 12, qx + 12 + i * 12, qy + 12 + j * 12),
                            fill=(*INK, 255))

    # 外框
    d.rectangle((10, 10, W - 10, H - 10), outline=(*INK, 255), width=4)
    d.rectangle((20, 20, W - 20, H - 20), outline=(*GOLD, 255), width=2)

    if isinstance(out, (str, Path)):
        p = Path(out)
        p.parent.mkdir(parents=True, exist_ok=True)
        img.convert("RGB").save(p, "PNG")
        return p
    img.convert("RGB").save(out, "PNG")
    return out
