# -*- coding: utf-8 -*-
"""立绘一键导入：把生成的图片放进项目并自动处理成可用格式。

用法：
    python scripts/import_portraits.py [图片来源文件夹]

匹配规则（命中其一即可）：
    1. 文件名含人物 id（如 wang_wei.png、xin_qiji.jpg）
    2. 文件名含人物中文名（如 王维.png、辛弃疾.jpg）
    3. 纯数字文件名（1.png ~ 18.png）按 portrait_prompts.md 的编号顺序对应

处理：
    - 转 RGBA；若图片无透明通道，自动做「边缘白底泛洪移除」抠出纯色背景
      （AI 生图工具大多支持透明背景/抠图，优先用工具自带抠图，效果更好）
    - 居中裁剪到 2:3 比例后缩放为 512x768，同名覆盖 assets/characters/{id}.png
    - 清空进程内立绘缓存
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from PIL import Image, ImageDraw

from config import CHAR_DIR
from data.people import PEOPLE

EXPECTED = (512, 768)

# 按 portrait_prompts.md 编号顺序（纯数字文件名时使用）
ORDER = ["wang_wei", "xin_qiji", "du_fu", "li_bai", "su_shi", "qu_yuan", "lu_you",
         "li_qingzhao", "zhang_jiuling", "li_yu", "tsangyang_gyatso", "nalan_xingde",
         "bi_sheng", "zhuge_liang", "zhang_heng", "shen_kuo", "bai_juyi"]


def _is_white(pixel: tuple, tol: int = 12) -> bool:
    return pixel[3] == 0 or (pixel[0] > 255 - tol and pixel[1] > 255 - tol and pixel[2] > 255 - tol)


def remove_white_bg(img: Image.Image, tol: int = 12) -> Image.Image:
    """边缘泛洪：从四边出发，把与纯白近似的连通背景挖成透明。"""
    img = img.convert("RGBA")
    w, h = img.size
    px = img.load()
    visited = [[False] * w for _ in range(h)]
    stack = []
    for x in range(w):
        stack += [(x, 0), (x, h - 1)]
    for y in range(h):
        stack += [(0, y), (w - 1, y)]
    while stack:
        x, y = stack.pop()
        if not (0 <= x < w and 0 <= y < h) or visited[y][x]:
            continue
        visited[y][x] = True
        if not _is_white(px[x, y], tol):
            continue
        px[x, y] = (255, 255, 255, 0)
        stack += [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]
    return img


def center_crop_to_ratio(img: Image.Image, ratio: tuple[int, int]) -> Image.Image:
    """居中裁剪到目标宽高比（不拉伸变形）。"""
    tw, th = ratio
    w, h = img.size
    target = tw / th
    cur = w / h
    if cur > target:      # 过宽：裁左右
        nw = int(h * target)
        x = (w - nw) // 2
        return img.crop((x, 0, x + nw, h))
    nh = int(w / target)  # 过高：裁上下
    y = (h - nh) // 2
    return img.crop((0, y, w, y + nh))


def find_source(person: dict, files: list[Path], index: int) -> Path | None:
    """按 id / 中文名 / 数字编号匹配源文件。

    数字编号按 portrait_prompts.md 的顺序：1=王维 2=辛弃疾 … 18=白居易。
    """
    name_hits = [
        f for f in files
        if f.stem.lower() == person["id"].lower() or person["name"] in f.stem
    ]
    if name_hits:
        return name_hits[0]
    if person["id"] in ORDER:
        num = ORDER.index(person["id"]) + 1
        for f in files:
            stem = f.stem.strip()
            if stem in (str(num), str(num).zfill(2)):
                return f
    return None


def process_one(person: dict, src: Path, out_dir: Path) -> str:
    with Image.open(src) as im:
        img = im.convert("RGBA")
    if img.mode != "RGBA" or img.getchannel("A").getextrema()[0] == 255:
        img = remove_white_bg(img)  # 无透明通道 → 自动抠白底
    img = center_crop_to_ratio(img, EXPECTED)
    img = img.resize(EXPECTED, Image.LANCZOS)
    out = out_dir / f"{person['id']}.png"
    img.save(out, "PNG")
    return str(out)


def main():
    src_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.home() / "Desktop" / "立绘"
    if not src_dir.is_dir():
        print(f"未找到图片来源文件夹：{src_dir}")
        print("用法：python scripts/import_portraits.py <图片来源文件夹>")
        return 2
    files = [f for f in sorted(src_dir.iterdir())
             if f.is_file() and f.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp")]
    if not files:
        print(f"文件夹里没有图片：{src_dir}")
        return 2

    print(f"== 立绘导入（来源：{src_dir}，共 {len(files)} 张）==")
    CHAR_DIR.mkdir(parents=True, exist_ok=True)
    missing = []
    for i, person in enumerate(PEOPLE):
        src = find_source(person, files, i)
        if src is None:
            missing.append(f"{person['name']}（{person['id']}）")
            continue
        out = process_one(person, src, CHAR_DIR)
        print(f"  ✓ {person['name']} <- {src.name} -> {out}")

    from core.photo_utils import _load_character
    _load_character.cache_clear()
    print(f"---\n导入完成：{len(PEOPLE) - len(missing)}/{len(PEOPLE)}")
    if missing:
        print("未匹配到源文件的人物：")
        for m in missing:
            print(f"  ✗ {m}")
        print("提示：把文件名改成人物 id 或中文名（如 wang_wei.png / 王维.png）后重跑。")
        return 1
    print("全部导入 ✅ 可运行 python scripts/check_portraits.py 复核。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
