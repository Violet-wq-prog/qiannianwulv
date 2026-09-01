# -*- coding: utf-8 -*-
"""入口A·步2：游玩偏好采集（多选 + 自由想法）+ 路线模式 A/B 选择。"""
import streamlit as st

from config import MODE_OPTIONS, PREF_OPTIONS, Page
from core import state
from core.data_loader import get_person
from views.common import goto, person_avatar


def render():
    if not state.guard("person_ids"):
        st.rerun()
        return
    t = state.travel()
    person = get_person(t["person_ids"][0])

    st.markdown("## ✍️ 游兴相告 · 告诉古人你想怎么玩")
    left, right = st.columns([1, 3])
    with left:
        person_avatar(person["id"], width=110)
    with right:
        st.markdown(f"同行人物：**{person['name']}**（{person['dynasty']}{person['category']}）")
        st.markdown(f"旅程地点：**{t['city']}**（检索词：{t['query']}）")
        st.markdown('<div class="qn-quote">AI 将融合【你的游玩喜好】与【' + person["name"] +
                    '的真实生平爱好经历】，共同生成成套路线。</div>', unsafe_allow_html=True)

    st.markdown("#### 你的游玩偏好（可多选，不选也行）")
    prefs = st.multiselect(
        "选择偏好的游法",
        PREF_OPTIONS,
        default=t.get("preferences") or [],
        key="pref_options",
    )
    if not prefs:
        st.caption("未选偏好也没关系——AI 将完全按" + person["name"] +
                   "的真实足迹与心迹为你安排行程。")
    notes = st.text_area(
        "还有什么想法，尽管说来（选填）",
        value=t.get("notes", ""),
        key="pref_notes",
        placeholder="例：我喜欢慢一点的节奏，最好多安排些老字号美食；想听和苏轼有关的故事……",
    )

    st.markdown("#### 游历天数")
    day_options = {"1 天": 1, "2 天": 2, "3 天": 3, "由 AI 安排": None}
    cur_days = t.get("days_choice")
    cur_label = next((l for l, v in day_options.items() if v == cur_days), "由 AI 安排")
    days_label = st.pills(
        "想玩几天？", options=list(day_options.keys()),
        default=list(day_options.keys())[list(day_options.keys()).index(cur_label)],
        key="pref_days")
    days_choice = day_options[days_label]

    st.markdown("#### 路线生成模式")
    mode = st.radio("选择模式", options=list(MODE_OPTIONS.keys()),
                    format_func=lambda m: MODE_OPTIONS[m],
                    index=1 if t.get("mode") == "dual" else 0, key="pref_mode")

    st.markdown("---")
    b1, b2 = st.columns([2, 1])
    with b1:
        if st.button("🧭 生成成套游历路线", type="primary", key="pref_gen"):
            t["preferences"] = prefs
            t["notes"] = notes
            t["mode"] = mode
            t["days_choice"] = days_choice
            t["route"] = None
            t["site_unlocked"] = []
            t["site_dialog"] = []
            t["dialog_site"] = None
            goto(Page.ROUTE_GEN)
    with b2:
        if st.button("← 重新选人", key="pref_back"):
            goto(Page.EXPLORE)
