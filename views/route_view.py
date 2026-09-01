# -*- coding: utf-8 -*-
"""路线总览：古风 SVG 地图（点亮状态）+ 成套站点卡片（点击进故地重游对话）。"""
import streamlit as st

from config import Page
from core import state
from core.ai_client import ai_disabled
from core.data_loader import get_person
from core.interactive_map import build_sites_deck
from core.svg_map import render_route_svg, svg_wrap_html
from views.common import button_row, goto, person_avatar, stamp_html


@st.cache_data(ttl=24 * 3600, show_spinner=False)
def _cached_export(kind: str, route_json: str, person_id: str, trip_id: int,
                   created_at: str) -> bytes:
    """导出字节缓存：同路线同参数不重复生成。失败 raise 不缓存。"""
    from core.export import export_bytes
    data = export_bytes(kind, route_json, person_id, trip_id, created_at)
    if not data:
        raise RuntimeError("导出内容为空")
    return data


def _render_real_map(t: dict, route: dict, unlocked: list[bool]):
    """实景交互地图：pydeck 站点散点，点击选中 → 跳该站对话。"""
    deck = build_sites_deck(route, unlocked, offline=ai_disabled())
    if deck is None:
        st.caption("路线站点暂无坐标信息，请先查看画卷地图。")
        return
    ev = st.pydeck_chart(deck, key="route_map", on_select="rerun",
                         selection_mode="single-object", width="stretch", height=420)
    sel = ev.selection if ev is not None else None
    objects = sel.get("objects") if sel else None
    if objects and objects.get("sites"):
        row = objects["sites"][0]
        idx = next((i for i, s in enumerate(route["sites"])
                    if s["place_id"] == row.get("place_id")), None)
        if idx is not None:
            # 消费事件后立即重置 widget 状态，防止 rerun 后旧 selection 循环跳站
            st.session_state["route_map"] = {"selection": {"indices": {}, "objects": {}}}
            t["site_idx"] = idx
            goto(Page.SITE_DIALOGUE)
            st.rerun()


def render():
    if not state.guard("route", "site_unlocked"):
        st.rerun()
        return
    t = state.travel()
    route = t["route"]
    person = get_person(route["person_ids"][0])
    unlocked = t["site_unlocked"]
    n = len(route["sites"])
    done = state.unlocked_count(t)

    if st.session_state.get("photo_hint"):
        st.info(st.session_state.pop("photo_hint"))

    st.markdown(f"## 🗺️ {route['route_name']}")
    left, right = st.columns([1, 3])
    with left:
        person_avatar(person["id"], width=100)
    with right:
        st.markdown('<div class="qn-quote">' + route["preface"] + "</div>", unsafe_allow_html=True)
        m1, m2, m3 = st.columns(3)
        m1.metric("路线天数", f"{route['days']} 天")
        m2.metric("已游站点", f"{done} / {n}")
        m3.metric("同行人物", person["name"])

    # 双地图：画卷 SVG（古风）+ 实景交互地图（pydeck，点击站点直达对话）
    tab_paint, tab_real = st.tabs(["🖌 画卷地图", "🗺 实景地图"])
    with tab_paint:
        # SVG 画卷地图（响应式包装：容器宽等比缩放，移动端不溢出；下载给纯 SVG）
        svg = render_route_svg(route, unlocked)
        st.html(svg_wrap_html(route, unlocked))
        st.download_button("⬇ 下载路线画卷（SVG）", svg.encode("utf-8"),
                           file_name=f"{route['route_name']}.svg", mime="image/svg+xml",
                           key="route_download")
    with tab_real:
        _render_real_map(t, route, unlocked)
        st.caption("点击地图上的站点圆点，可直接前往该站与古人对话。")

    st.markdown("---")
    st.markdown("#### 📍 成套路线站点")
    for i, s in enumerate(route["sites"]):
        with st.container(border=True):
            c1, c2, c3 = st.columns([1, 4.5, 1.4])
            with c1:
                tag = st.markdown
                if unlocked[i]:
                    tag(f'<div style="margin-top:.4rem">' + stamp_html("已游") + "</div>",
                        unsafe_allow_html=True)
                else:
                    tag(f'<div style="margin-top:.4rem;color:#8a7c66;letter-spacing:.2em;">'
                        f'第{s["day"]}天·第{s["seq"]}站</div>', unsafe_allow_html=True)
            with c2:
                st.markdown(f"**{s['stop_title']}**（{s['place_name']}）")
                st.caption(s["story"][:90] + ("…" if len(s["story"]) > 90 else ""))
                st.markdown(f"<span style='color:#8a7c66;font-size:.85rem'>💡 {s['tip']}</span>",
                            unsafe_allow_html=True)
            with c3:
                if unlocked[i]:
                    label = "再访对话"
                else:
                    label = "前往对话"
                if st.button(label, key=f"route_site_{i}",
                             type="primary" if not unlocked[i] else "secondary"):
                    t["site_idx"] = i
                    goto(Page.SITE_DIALOGUE)

    st.markdown("---")
    with st.expander("📤 导出与分享"):
        _export_row(route, person, t)

    st.markdown("---")
    specs = [
        {"label": "← 调整偏好重新规划", "key": "route_replan",
         "on_click": _replan},
    ]
    if done == n and n:
        specs += [
            {"label": "📸 去生成同游合影", "key": "route_photo", "type": "primary",
             "on_click": lambda: goto(Page.PHOTO)},
            {"label": "📝 写游历随笔", "key": "route_journal",
             "on_click": lambda: goto(Page.JOURNAL)},
        ]
    button_row(specs)


def _export_row(route: dict, person: dict, t: dict):
    """路线导出：长图 + 行程单（字节缓存，rerun 不重复生成）。"""
    import json
    from core import database
    from core.export import export_bytes
    route_json = json.dumps(route, ensure_ascii=False, sort_keys=True)
    trip_id = t.get("trip_id") or 0
    created_at = (database.get_trip(trip_id)["created_at"] if trip_id else "")
    c1, c2 = st.columns(2)
    with c1:
        try:
            png = _cached_export("long_image", route_json, person["id"], trip_id, created_at)
            st.download_button("⬇ 路线长图（PNG）", png, file_name="路线长图.png",
                               mime="image/png", key="export_long")
        except RuntimeError:
            st.caption("长图生成失败，稍后再试。")
    with c2:
        md = _cached_export("md", route_json, person["id"], trip_id, created_at)
        st.download_button("⬇ 行程单（Markdown）", md, file_name="行程单.md",
                           mime="text/markdown", key="export_md")


def _replan():
    """清空旧路线回偏好页（同参数重新生成会命中 P3 缓存，不再重复付费）。"""
    t = state.travel()
    t["route"] = None
    t["site_unlocked"] = []
    goto(Page.PREFERENCE)
