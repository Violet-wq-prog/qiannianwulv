# -*- coding: utf-8 -*-
"""入口A·步1：地点检索 → 匹配在此地生活游历过的历史人物 → 选定同行人物。"""
import streamlit as st

from config import Page
from core import state
from core.data_loader import get_place, people_at_places, resolve_place_query
from core.geo import render_gps_block
from views.common import goto, person_avatar


def render():
    st.markdown("## 🗺️ 寻访故地 · 选定同行古人")
    st.caption("输入城市或景点（如：杭州、西湖、长安、黄州），检索在此地留下故事的历史人物。")

    with st.expander("📍 看看你附近的故地（定位）"):
        render_gps_block()

    query = st.text_input("想去哪里？", key="explore_query", placeholder="例：杭州 / 西湖 / 长安 / 黄州 / 南阳")
    if st.button("检索此地故人", type="primary", key="explore_search", disabled=not query.strip()):
        st.session_state["explore_result_query"] = query.strip()
        st.rerun()

    q = st.session_state.get("explore_result_query", "")
    if not q:
        st.markdown('<div class="qn-quote">试一个地点吧——千年之中，总有人曾在此停留。</div>',
                    unsafe_allow_html=True)
        return

    place_ids = resolve_place_query(q)
    if not place_ids:
        st.warning(f"未检索到与「{q}」相关的故地。试试：杭州、西湖、黄州、长安、洛阳、南阳、济南……")
        return

    places = [get_place(pid) for pid in place_ids]
    people = people_at_places(place_ids)
    if not people:
        st.warning(f"「{q}」相关的故地暂未收录人物事迹，可先看看其他地点。")
        return

    st.success(f"在「{q}」找到 {len(places)} 处故地、{len(people)} 位曾在此留下故事的历史人物。")
    st.markdown("#### 请选一位作为本次旅程的同行人物")

    for i, p in enumerate(people):
        with st.container(border=True):
            left, right = st.columns([1, 3])
            with left:
                person_avatar(p["id"], width=110)
            with right:
                st.markdown(f"**{p['name']}** · {p['dynasty']}{p['category']} · {p['lifespan']}")
                st.caption(p["brief"])
                st.markdown('<div class="qn-quote">「' + p["quote"] + "」</div>", unsafe_allow_html=True)
                st.markdown("**在此地的事迹：**")
                for e in p["matched_entries"]:
                    st.markdown(f"- 📍 {get_place(e['place_id'])['name']}：{e['note']}")
                b1, b2, b3 = st.columns([1.4, 1, 1])
                with b1:
                    if st.button("✨ 选TA同行", key=f"explore_pick_{p['id']}", type="primary"):
                        t = state.travel()
                        if t is None or t.get("query") != q:
                            t = state.start_travel(q, _main_city(place_ids), place_ids)
                        t["candidate_people"] = people
                        t["person_ids"] = [p["id"]]
                        goto(Page.PREFERENCE)
                with b2:
                    if st.button("看小传", key=f"explore_profile_{p['id']}"):
                        st.session_state[state.KEY_PROFILE_PERSON] = p["id"]
                        st.session_state[state.KEY_PROFILE_RETURN] = Page.EXPLORE
                        goto(Page.PERSON_PROFILE)
                with b3:
                    if st.button("拉进群聊候选", key=f"explore_pool_{p['id']}"):
                        pool = st.session_state[state.KEY_GROUP_POOL]
                        if p["id"] not in pool:
                            pool.append(p["id"])
                        st.toast(f"已将 {p['name']} 加入群聊候选")


def _main_city(place_ids: list[str]) -> str:
    """取结果中第一处地点的城市作为旅程城市。"""
    return get_place(place_ids[0])["city"]
