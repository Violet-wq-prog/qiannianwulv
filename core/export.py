# -*- coding: utf-8 -*-
"""导出与分享：路线长图（PNG）、行程单（Markdown）、分享卡片（票根 + 真二维码）。

全部复用 photo_utils 的字体缓存与构图元素；输出走 BytesIO（零临时文件）。
qrcode 未安装时分享卡片自动降级为票根自带伪二维码。
"""
import io
import json
from pathlib import Path

from PIL import Image, ImageDraw

from core.photo_utils import _draw_seal, find_cn_font, make_ticket

LONG_W = 900
HEADER_H = 300
SITE_H = 220
FOOTER_H = 150
INK = (58, 50, 38)
GOLD = (176, 141, 79)
GRAY = (138, 124, 102)


def _paper(W: int, H: int) -> Image.Image:
    """宣纸渐变底（与票根一致）。"""
    img = Image.new("RGBA", (W, H), (250, 244, 231, 255))
    d = ImageDraw.Draw(img)
    for y in range(H):
        t = y / H
        d.line([(0, y), (W, y)], fill=(int(250 - 14 * t), int(244 - 16 * t), int(231 - 18 * t), 255), width=1)
    return img


def _wrap_cjk(text: str, per_line: int) -> list[str]:
    """按字符数折行（中文全角等宽，直接切片；保留标点可接受的断行）。"""
    text = (text or "").strip()
    return [text[i:i + per_line] for i in range(0, len(text), per_line)] or [""]


def route_long_image(route: dict, person: dict, out) -> Path | io.BytesIO:
    """路线长图：标题/引子/逐站故事/印章，竖版宣纸风格。"""
    n = len(route["sites"])
    H = HEADER_H + SITE_H * n + FOOTER_H
    img = _paper(LONG_W, H)
    d = ImageDraw.Draw(img)

    f_title = find_cn_font(46)
    f_mid = find_cn_font(28)
    f_body = find_cn_font(24)
    f_small = find_cn_font(20)

    # 页眉
    d.text((70, 54), route["route_name"], font=f_title, fill=INK)
    y = 130
    mode = "人物视角优先" if route["mode"] == "person_lead" else "双向融合"
    d.text((74, y), f"{route['city']} · {route['days']} 天 {n} 站 · {mode}"
            f" · 同行 {person['name']}（{person['dynasty']}{person['category']}）",
           font=f_mid, fill=GRAY)
    y += 54
    for line in _wrap_cjk(route.get("preface", ""), 38):
        d.text((74, y), line, font=f_body, fill=INK)
        y += 40
    d.line((70, y + 6, LONG_W - 70, y + 6), fill=GOLD, width=2)

    # 逐站
    for i, s in enumerate(route["sites"]):
        y0 = HEADER_H + SITE_H * i
        d.text((74, y0 + 22), f"第{s['day']}天 · 第{s['seq']}站 ｜ {s['place_name']}",
               font=f_mid, fill=INK)
        if s.get("stop_title") and s["stop_title"] != s["place_name"]:
            d.text((LONG_W - 74 - len(s["stop_title"]) * 28, y0 + 22),
                   s["stop_title"], font=f_small, fill=(192, 57, 43))
        yy = y0 + 70
        for line in _wrap_cjk(s.get("story", ""), 40)[:3]:  # 每站故事最多 3 行
            d.text((74, yy), line, font=f_body, fill=INK)
            yy += 40
        d.text((74, y0 + SITE_H - 52), f"💡 {s.get('tip', '')}", font=f_small, fill=GRAY)
        if i < n - 1:
            d.line((74, y0 + SITE_H - 16, LONG_W - 74, y0 + SITE_H - 16),
                   fill=(201, 187, 156), width=1)

    # 页脚印章
    _draw_seal(d, LONG_W - 74 - 96, H - FOOTER_H + 24, "千年晤旅", size=48)
    d.text((74, H - 60), "—— 与古人同游故地，听亲历者讲往事 ——", font=f_small, fill=GRAY)
    d.rectangle((12, 12, LONG_W - 12, H - 12), outline=INK, width=4)
    d.rectangle((22, 22, LONG_W - 22, H - 22), outline=GOLD, width=2)

    return _save(img, out)


def itinerary_md(route: dict, person: dict, checkins: list = None,
                 journals: list = None) -> str:
    """行程单（Markdown）：可直接复制分享或存档。"""
    checkins = checkins or []
    journals = journals or []
    done_keys = {c["site_key"] for c in checkins}
    lines = [
        f"# {route['route_name']}",
        "",
        f"- 地点：{route['city']} · {route['days']} 天 {len(route['sites'])} 站",
        f"- 同行古人：{person['name']}（{person['dynasty']}{person['category']}）",
        f"- 路线模式：{'人物视角优先' if route['mode'] == 'person_lead' else '双向融合'}",
        f"- 来自：🏮 千年晤旅 · 沉浸式历史人文游历平台",
        "",
        f"> {route.get('preface', '')}",
        "",
        "## 行程",
        "",
    ]
    for s in route["sites"]:
        mark = "✅" if s["place_id"] in done_keys else "🔒"
        lines += [
            f"### {mark} 第{s['day']}天 · 第{s['seq']}站 {s['place_name']}",
            f"{s.get('story', '')}",
            f"*💡 {s.get('tip', '')}*",
            "",
        ]
    if checkins:
        lines += ["## 打卡记录", ""]
        for c in checkins:
            lines.append(f"- {c['site_name']} · {c['unlocked_at']}")
        lines.append("")
    if journals:
        lines += ["## 游历随笔", ""]
        for r in journals:
            lines += [r["content"], f"*{r['created_at']}*", ""]
    return "\n".join(lines)


def share_card_bytes(route: dict, person: dict, trip_id: int, created_at: str) -> bytes:
    """分享卡片：票根构图 + 真二维码（覆盖伪二维码区域）；qrcode 缺失时原样返回票根。"""
    buf = io.BytesIO()
    make_ticket(route, person, trip_id, created_at, buf)
    qr = _real_qr(
        f"千年晤旅·《{route['route_name']}》·同行{person['name']}·旅程#{trip_id}"
    )
    if qr is None:
        return buf.getvalue()
    img = Image.open(buf).convert("RGB")
    qr = qr.resize((130, 130), Image.LANCZOS)
    img.paste(qr, (430, 700))  # 票根伪二维码区域（W-190=430, y=700）
    out = io.BytesIO()
    img.save(out, "PNG")
    return out.getvalue()


def _real_qr(content: str) -> Image.Image | None:
    try:
        import qrcode
        qr = qrcode.QRCode(border=2, box_size=8)
        qr.add_data(content)
        qr.make(fit=True)
        return qr.make_image(fill_color="black", back_color="white").convert("RGB")
    except ImportError:
        return None


def _save(img: Image.Image, out) -> Path | io.BytesIO:
    if isinstance(out, (str, Path)):
        p = Path(out)
        p.parent.mkdir(parents=True, exist_ok=True)
        img.convert("RGB").save(p, "PNG")
        return p
    img.convert("RGB").save(out, "PNG")
    return out


def export_bytes(kind: str, route_json: str, person_id: str, trip_id: int,
                 created_at: str, checkins_json: str = "[]", journals_json: str = "[]") -> bytes:
    """统一导出入口（供 st.cache_data 包装）：kind ∈ long_image / md / share_card。

    route_json 等以字符串传入（可哈希、随旅程内容参与缓存 key）。
    """
    from core.data_loader import build_index
    route = json.loads(route_json)
    person = build_index()["people_by_id"][person_id]
    checkins = json.loads(checkins_json or "[]")
    journals = json.loads(journals_json or "[]")
    if kind == "long_image":
        buf = io.BytesIO()
        route_long_image(route, person, buf)
        return buf.getvalue()
    if kind == "md":
        return itinerary_md(route, person, checkins, journals).encode("utf-8")
    if kind == "share_card":
        return share_card_bytes(route, person, trip_id, created_at)
    raise ValueError(f"未知导出类型：{kind}")
