# -*- coding: utf-8 -*-
"""立绘校验：遍历人物库检查 assets/characters/{id}.png 的透明通道与尺寸，
输出「立绘就绪 N/18」报告，帮助确认哪些仍是程序占位图。

运行：python scripts/check_portraits.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# 管道/重定向输出时统一切到 UTF-8，避免 ✓/✗/✅ 在 GBK 编码下崩溃（见 smoke_test.py 同款处理）
if sys.stdout and sys.stdout.encoding and "utf" not in sys.stdout.encoding.lower():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from PIL import Image

from config import CHAR_DIR
from data.people import PEOPLE

EXPECTED = (512, 768)


def inspect_portrait(path: Path) -> dict:
    try:
        with Image.open(path) as im:
            has_alpha = im.mode in ("RGBA", "LA") or (im.mode == "P" and "transparency" in im.info)
            # 抽样四角像素的 alpha：透明底图片四角应接近 0
            rgba = im.convert("RGBA")
            w, h = rgba.size
            corners = [rgba.getpixel(p) for p in [(0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)]]
            transparent_bg = all(c[3] < 10 for c in corners)
            return {
                "exists": True, "size": (w, h), "mode": im.mode,
                "has_alpha": has_alpha, "transparent_bg": transparent_bg,
                "match": (w, h) == EXPECTED,
            }
    except OSError:
        return {"exists": False}


def main():
    print("== 千年晤旅 · 立绘校验 ==")
    ready, issues = 0, []
    for p in PEOPLE:
        path = CHAR_DIR / f"{p['id']}.png"
        info = inspect_portrait(path)
        if not info["exists"]:
            issues.append(f"{p['name']}（{p['id']}）：文件缺失")
            continue
        flags = []
        if not info["has_alpha"]:
            flags.append("无透明通道")
        if not info["transparent_bg"]:
            flags.append("四角非透明（可能是白底）")
        if not info["match"]:
            flags.append(f"尺寸 {info['size'][0]}x{info['size'][1]}（建议 {EXPECTED[0]}x{EXPECTED[1]}）")
        if flags:
            issues.append(f"{p['name']}（{p['id']}）：{'；'.join(flags)}")
        else:
            ready += 1
            print(f"  ✓ {p['name']} · {info['size'][0]}x{info['size'][1]} 透明底")
    print(f"---\n立绘就绪 {ready}/{len(PEOPLE)}")
    if issues:
        print("待处理：")
        for i in issues:
            print(f"  ✗ {i}")
        print("提示：用 portrait_prompts.md 的提示词生成 512x768 透明底 PNG，同名覆盖后重跑本脚本。")
    else:
        print("全部立绘就绪 ✅")
    return 0 if ready == len(PEOPLE) else 1


if __name__ == "__main__":
    sys.exit(main())
