# -*- coding: utf-8 -*-
"""人物详情页：生平小传、事迹、爱好、关联地点，并可由此进入对话/群聊/同行。"""
import streamlit as st

from config import Page
from core import state
from core.data_loader import get_person, get_place
from views.common import button_row, goto, person_avatar


def render():
    pid = st.session_state.get(state.KEY_PROFILE_PERSON)
    person = get_person(pid) if pid else None
    if person is None:
        st.info("尚未选择人物。")
        goto(Page.HOME)
        st.rerun()
        return

    left, right = st.columns([1, 3])
    with left:
        person_avatar(pid, width=170)
    with right:
        st.markdown(f"## {person['name']} · {person['lifespan']}")
        st.markdown(f"**{person['dynasty']} · {person['category']}**")
        st.markdown(f"性格：{person['personality']}")
        st.markdown(f"爱好：{'、'.join(person['hobbies'])}")
        st.markdown('<div class="qn-quote">「' + person["quote"] + "」</div>", unsafe_allow_html=True)

    st.markdown("#### 生平")
    st.write(person["brief"])

    st.markdown("#### 一生所成")
    for a in person["achievements"]:
        st.markdown(f"- {a}")

    st.markdown("#### 故地足迹")
    for e in person.get("places", []):
        place = get_place(e["place_id"])
        if place:
            st.markdown(f"- 📍 **{place['name']}**（{place['city']}）：{e['note']}")

    st.markdown("#### 听他/她本人说")
    st.markdown('<div class="qn-quote">' + person["self_talk"] + "</div>", unsafe_allow_html=True)

    st.markdown("---")
    t = state.travel()
    specs = [
        {"label": "💬 与TA畅谈", "key": "profile_solo", "type": "primary",
         "on_click": lambda: _start_solo(pid)},
        {"label": "加入群聊候选", "key": "profile_pool",
         "on_click": lambda: _add_to_pool(pid, person)},
        {"label": "返回", "key": "profile_back",
         "on_click": lambda: goto(st.session_state.get(state.KEY_PROFILE_RETURN, Page.HOME))},
    ]
    if t and t.get("person_ids"):
        specs.append({"label": "✨ 选TA同行", "key": "profile_travel",
                      "on_click": lambda: _travel_with(t, pid)})
    button_row(specs)


def _start_solo(pid: str):
    st.session_state[state.KEY_SOLO_PERSON] = pid
    goto(Page.CHAT_SOLO)


def _add_to_pool(pid: str, person: dict):
    pool = st.session_state[state.KEY_GROUP_POOL]
    if pid not in pool:
        pool.append(pid)
        st.toast(f"已将 {person['name']} 加入群聊候选")
    else:
        st.toast("已在候选池中")


def _travel_with(t: dict, pid: str):
    t["person_ids"] = [pid]
    t["route"] = None          # 换人则旧路线作废
    t["site_unlocked"] = []
    goto(Page.PREFERENCE)
