# -*- coding: utf-8 -*-
"""路线生成页：进入即触发（幂等：route 已存在则不重复调用 AI）。

AI 结构化输出失败时整体降级为内置路线（人物库预写文本拼装），保证演示不中断。
"""
import streamlit as st

from config import Page
from core import database, state
from core.ai_client import ai_available, ai_enabled, chat_json
from core.data_loader import build_index, enrich_entries, get_person, person_entries_in_city
from core.prompt_templates import build_route_messages
from core.route_builder import build_fallback_route, normalize_route
from views.common import goto, person_avatar


@st.cache_data(ttl=60 * 60 * 24, show_spinner=False)
def _cached_route_raw(person_id: str, city: str, place_ids: tuple,
                      prefs: tuple, notes: str, mode: str, days: int | None):
    """确定性路线生成缓存：同参数（同人物/同城/同偏好/同模式/同天数）不再重复付费。

    铁律：缓存函数内不碰 session_state——数据用 build_index() 纯函数重建，
    AI 可用性用 ai_enabled() 纯函数判断；失败 raise（异常不进缓存，避免断网冻结）。
    """
    if not ai_enabled():
        raise RuntimeError("AI 不可用，跳过缓存")
    index = build_index()
    person = index["people_by_id"][person_id]
    entries = [e for e in person["places"]
               if index["places_by_id"][e["place_id"]]["city"] == city]
    entries = [{**e, "place": index["places_by_id"][e["place_id"]]} for e in entries]
    result = chat_json(build_route_messages(person, city, entries, list(prefs), notes, mode, days))
    if result is None:
        raise RuntimeError("AI 路线解析失败，跳过缓存")
    return result


def render():
    if not state.guard("person_ids"):
        st.rerun()
        return
    t = state.travel()
    person = get_person(t["person_ids"][0])

    st.markdown("## 🧭 正在为你与古人合谋一条路线……")

    if t.get("route"):
        _render_result(t, person)
        return

    entries = enrich_entries(person_entries_in_city(person, t["city"]))
    if not entries:
        st.warning(f"人物库中暂未收录 {person['name']} 在「{t['city']}」的足迹，"
                   "请返回换个地点或换位同行人物。")
        if st.button("← 返回寻访故地"):
            goto(Page.EXPLORE)
        return

    with st.spinner("AI 正在融合你的喜好与" + person["name"] + "的生平经历，编排成套路线……"):
        days = t.get("days_choice")
        raw = None
        if ai_available():  # session 级把关（AppTest 可强制离线）；缓存函数内部另有 env 级把关
            try:
                raw = _cached_route_raw(person["id"], t["city"], tuple(t["place_ids"]),
                                        tuple(t["preferences"]), t["notes"] or "", t["mode"], days)
            except RuntimeError:
                raw = None  # AI 不可用或生成失败：走离线降级
        route = normalize_route(raw, person, t["city"], entries, t["mode"], days)
        source = "ai"
        if route is None:
            route = build_fallback_route(person, t["city"], entries,
                                         t["preferences"], t["mode"], days)
            source = "fallback"

    t["route"] = route
    t["route_source"] = source
    t["site_unlocked"] = [False] * len(route["sites"])
    t["site_idx"] = 0
    t["dialog_site"] = None
    t["site_dialog"] = []
    if t.get("trip_id") is None:
        t["trip_id"] = database.create_trip(
            t["city"], route["route_name"], t["mode"], [person["id"]],
            {"preferences": t["preferences"], "notes": t["notes"]}, route)
    st.rerun()


def _render_result(t: dict, person: dict):
    route = t["route"]
    src = t.get("route_source", "ai")
    if src == "ai":
        st.success("✨ AI 已按你的喜好与" + person["name"] + "的生平经历，生成了一套完整路线。")
    else:
        st.info("📜 当前为离线演示模式：路线由内置的" + person["name"] + "足迹故事编排而成，同样成套可游。")

    left, right = st.columns([1, 3])
    with left:
        person_avatar(person["id"], width=110)
    with right:
        st.markdown(f"### {route['route_name']}")
        st.markdown(f"**{route['days']} 天 · {len(route['sites'])} 站** · 模式："
                    f"{'人物视角优先' if route['mode']=='person_lead' else '双向融合'}")
        st.markdown('<div class="qn-quote">' + route["preface"] + "</div>", unsafe_allow_html=True)
    if st.button("🗺️ 查看完整路线地图", type="primary", key="route_gen_view"):
        goto(Page.ROUTE_VIEW)
