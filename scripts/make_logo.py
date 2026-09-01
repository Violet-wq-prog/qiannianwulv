# -*- coding: utf-8 -*-
"""生成报名用项目 Logo（512×512 PNG，古风印章风格，<5M）。"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from PIL import Image, ImageDraw

from config import PROJECT_ROOT
from core.photo_utils import find_cn_font

W = H = 512
OUT = PROJECT_ROOT / "submission" / "项目logo.png"

img = Image.new("RGBA", (W, H), (250, 244, 231, 255))
d = ImageDraw.Draw(img)
for y in range(H):
    t = y / H
    d.line([(0, y), (W, y)], fill=(int(250 - 12 * t), int(244 - 14 * t), int(231 - 16 * t), 255), width=1)

# 双线画框
INK = (58, 50, 38)
GOLD = (176, 141, 79)
d.rectangle((16, 16, W - 16, H - 16), outline=INK, width=6)
d.rectangle((28, 28, W - 28, H - 28), outline=GOLD, width=3)

# 主标题：千年晤旅（逐字）
title = "千年晤旅"
f_t = find_cn_font(120)
x = 256 - 240  # 粗略居中
for c in title:
    bb = d.textbbox((0, 0), c, font=f_t)
    w = bb[2] - bb[0]
    d.text((x + 3, 118 + 3), c, font=f_t, fill=(*INK, 90))
    d.text((x, 118), c, font=f_t, fill=(*INK, 255))
    x += w + 16

# 副标题
f_s = find_cn_font(30)
sub = "沉浸式历史人文游历"
bb = d.textbbox((0, 0), sub, font=f_s)
d.text(((W - (bb[2] - bb[0])) / 2, 330), sub, font=f_s, fill=(138, 124, 102, 255))

# 印章
seal = 88
sx, sy = (W - seal) / 2, 398
d.rounded_rectangle((sx, sy, sx + seal, sy + seal), radius=14, fill=(192, 57, 43, 255),
                    outline=(255, 255, 255, 150), width=3)
f_seal = find_cn_font(44)
d.text((sx + 22, sy + 24), "晤旅", font=f_seal, fill=(255, 250, 240, 255))

img.convert("RGB").save(OUT, "PNG")
print("Logo 已生成:", OUT, f"{OUT.stat().st_size//1024} KB")
