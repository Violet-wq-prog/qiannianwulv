# -*- coding: utf-8 -*-
"""交互实景地图：pydeck 散点 + 连线呈现路线站点，支持点击选中站点（配合 on_select 跳转对话）。

底图策略：默认 carto-positron 浅色底图（需联网加载瓦片）；
离线/断网时切换为无底图纯色模式，站点散点仍可点。
"""
import pydeck as pdk

DONE_COLOR = [192, 57, 43, 200]      # 印章红：已游
TODO_COLOR = [138, 124, 102, 200]    # 墨灰：未游
LINE_COLOR = [74, 59, 43, 180]       # 墨线
PAPER_RGB = [247, 241, 227]          # 宣纸米（无底图背景）


def _map_style(offline: bool) -> str:
    """离线/断网时无底图（纯色），否则浅色地图。"""
    return None if offline else "carto-positron"


def build_sites_deck(route: dict, unlocked: list[bool], offline: bool = False):
    """构造路线站点 pydeck Deck（可点击：pickable + id="sites"）。

    重要：所有访问器一律用数据行字段（"position"/"color" 等纯属性），
    不要写数组字面量表达式（如 get_position="[lng, lat]"）——deck.gl JSON 前端
    编译器对含数组字面量的表达式会报 "Unclosed ["，导致实景地图渲染失败。
    """
    rows = []
    for i, s in enumerate(route["sites"]):
        pl = _place_of(route, s)
        done = bool(unlocked[i]) if i < len(unlocked) else False
        lat, lng = pl.get("lat", 0.0), pl.get("lng", 0.0)
        rows.append({
            "place_id": s["place_id"],
            "name": s["place_name"],
            "day": s["day"],
            "seq": s["seq"],
            "done": done,
            "lat": lat,
            "lng": lng,
            "position": [lng, lat],
            "color": DONE_COLOR if done else TODO_COLOR,
            "line_color": [250, 246, 227, 220],
        })
    rows = [r for r in rows if r["lat"] or r["lng"]]  # 缺坐标的地点不入图
    if not rows:
        return None

    lines = [
        {"start": [rows[i]["lng"], rows[i]["lat"]],
         "end": [rows[i + 1]["lng"], rows[i + 1]["lat"]],
         "color": LINE_COLOR}
        for i in range(len(rows) - 1)
    ]
    center_lat = sum(r["lat"] for r in rows) / len(rows)
    center_lng = sum(r["lng"] for r in rows) / len(rows)

    layers = [
        pdk.Layer(
            "ScatterplotLayer",
            data=rows,
            get_position="position",
            get_radius=950,
            get_fill_color="color",
            get_line_color="line_color",
            line_width_min_pixels=2,
            pickable=True,
            id="sites",
        ),
    ]
    if lines:
        layers.insert(0, pdk.Layer(
            "LineLayer",
            data=lines,
            get_source_position="start",
            get_target_position="end",
            get_color="color",
            get_width=4,
        ))

    return pdk.Deck(
        map_style=_map_style(offline),
        map_provider="carto",
        initial_view_state=pdk.ViewState(
            latitude=center_lat, longitude=center_lng, zoom=_zoom_for(rows)),
        layers=layers,
        parameters={"clearColor": PAPER_RGB + [255]} if offline else None,
        tooltip={"html": "<b>{name}</b><br>第{day}天 · 第{seq}站",
                 "style": {
                     "backgroundColor": "#fdf6e3", "color": "#3a3226",
                     "fontFamily": "KaiTi, serif", "borderRadius": "4px",
                 }},
    )


def _zoom_for(rows: list[dict]) -> int:
    """按站点跨度估算缩放级别：跨省路线拉远，同城路线拉近。"""
    lats = [r["lat"] for r in rows]
    lngs = [r["lng"] for r in rows]
    span = max(max(lats) - min(lats), max(lngs) - min(lngs))
    if span < 0.5:
        return 10
    if span < 3:
        return 7
    if span < 10:
        return 5
    return 4


def _place_of(route: dict, site: dict) -> dict:
    """路线内联站点坐标（route 站点的 place 数据可能在 P7 前不含 lat/lng，
    故从数据层兜底取一次；单次渲染数据量小，无需缓存）。"""
    if "lat" in site and site.get("lat") is not None:
        return site
    from core.data_loader import get_place
    return get_place(site["place_id"]) or {}
