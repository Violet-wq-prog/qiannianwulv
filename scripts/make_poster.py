# -*- coding: utf-8 -*-
"""iCAN 产品海报生成：1200×560 横版，大字「千年晤旅」+ 副标题。

运行：python scripts/make_poster.py → submission/poster.jpg
"""
import sys
import zlib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from PIL import Image, ImageDraw, ImageFilter

from config import CHAR_DIR, PROJECT_ROOT
from core.photo_utils import find_cn_font

W, H = 1200, 560
PAPER = (250, 244, 231)
INK = (58, 50, 38)
SEAL = (192, 57, 43)


def _paper():
    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)
    for y in range(H):
        t = y / H
        d.line([(0, y), (W, y)], fill=(int(250 - 10 * t), int(244 - 12 * t), int(231 - 14 * t)), width=1)
    return img


def _mountains(d: ImageDraw.ImageDraw):
    r = zlib.crc32(b"poster")
    for layer, (base_y, alpha) in enumerate([(430, 70), (470, 100)]):
        pts = [(0, base_y + 60)]
        for i in range(0, W + 100, 100):
            y = base_y - ((zlib.crc32(f"{r}{layer}{i}".encode()) % 3) * 18) \
                - (zlib.crc32(f"m{layer}{i}".encode()) % 30)
            pts.append((i, y))
        pts += [(W, base_y + 60)]
        d.polygon(pts, fill=(58, 50, 38, alpha))
    # 淡月
    moon = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    md = ImageDraw.Draw(moon)
    md.ellipse((W - 240, 60, W - 170, 130), fill=(192, 57, 43, 55))
    return moon.filter(ImageFilter.GaussianBlur(4))


def _characters() -> Image.Image:
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    for pid, x, h in [("li_bai", -40, 340), ("su_shi", W - 320, 400)]:
        p = CHAR_DIR / f"{pid}.png"
        if not p.exists():
            continue
        im = Image.open(p).convert("RGBA")
        w = int(im.width * h / im.height)
        im = im.resize((w, h), Image.LANCZOS)
        im.putalpha(im.getchannel("A").point(lambda a: int(a * 0.55)))
        layer.alpha_composite(im, (x, H - h))
    return layer


def main():
    img = _paper().convert("RGBA")
    d = ImageDraw.Draw(img)
    img.alpha_composite(_mountains(d))
    img.alpha_composite(_characters())

    d = ImageDraw.Draw(img)
    # 大字题名（逐字拉开字距）
    title = "千年晤旅"
    font_t = find_cn_font(168)
    font_sub = find_cn_font(44)
    font_slogan = find_cn_font(30)
    char_w = sum(d.textbbox((0, 0), c, font=font_t)[2] - d.textbbox((0, 0), c, font=font_t)[0] for c in title)
    gap = 26
    total = char_w + gap * 3
    x = (W - total) / 2
    y = 150
    for c in title:
        d.text((x + 4, y + 4), c, font=font_t, fill=(*INK, 90))
        d.text((x, y), c, font=font_t, fill=(*INK, 255))
        x += d.textbbox((0, 0), c, font=font_t)[2] + gap

    sub = "沉浸式历史人文游历交互平台"
    bbox = d.textbbox((0, 0), sub, font=font_sub)
    d.text(((W - (bbox[2] - bbox[0])) / 2, y + 185), sub, font=font_sub, fill=(*INK, 235))

    slogan = "与古人同游故地 · 听亲历者讲往事"
    bbox = d.textbbox((0, 0), slogan, font=font_slogan)
    d.text(((W - (bbox[2] - bbox[0])) / 2, 480), slogan, font=font_slogan, fill=(138, 124, 102, 255))

    # 印章
    d.rounded_rectangle((70, 400, 150, 480), radius=12, fill=(*SEAL, 250),
                        outline=(255, 255, 255, 150), width=3)
    f_seal = find_cn_font(52)
    d.text((92, 412), "晤旅", font=f_seal, fill=(255, 250, 240, 255))

    # 双线画框
    d.rectangle((14, 14, W - 14, H - 14), outline=(*INK, 255), width=4)
    d.rectangle((24, 24, W - 24, H - 24), outline=(176, 141, 79, 255), width=2)

    # iCAN 专属要求：AI 生成素材角落小字标注「AI辅助制作」
    f_note = find_cn_font(18)
    d.text((W - 290, H - 42), "人物插画与画面由AI辅助制作", font=f_note,
           fill=(138, 124, 102, 200))

    out = PROJECT_ROOT / "submission" / "poster.jpg"
    out.parent.mkdir(parents=True, exist_ok=True)
    img.convert("RGB").save(out, "JPEG", quality=92)
    print("海报已生成:", out, out.stat().st_size // 1024, "KB")


if __name__ == "__main__":
    main()
