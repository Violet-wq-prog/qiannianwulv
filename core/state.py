# -*- coding: utf-8 -*-
"""session_state 状态机：页面跳转、travel 链路数据读写、前置守卫。

Streamlit 无服务端常驻进程，本模块只做 session_state 的薄封装：
所有数据以 travel dict 在 session 内闭环流转，SQLite 只做落盘副本。
"""
import streamlit as st

from config import Page

# —— session_state 键名 ——
KEY_PAGE = "page"
KEY_TRAVEL = "travel"
KEY_INDEX = "index"
KEY_GROUP_POOL = "group_pool"        # 群聊候选池 [person_id]
KEY_SOLO_MSGS = "solo_msgs"          # person_id -> [{"role","content"}]
KEY_SOLO_PERSON = "solo_person"      # 当前单人对话人物 id
KEY_SOLO_CONVO = "solo_convo_id"     # 落库会话 id
KEY_GROUP_MSGS = "group_msgs"        # [{"speaker","content"}]
KEY_GROUP_MEMBERS = "group_members"  # [person_id]
KEY_GROUP_OPENED = "group_opened"    # 群聊开场是否已生成（幂等守卫，防双击叠加 AI 调用）
KEY_GROUP_CONVO = "group_convo_id"
KEY_AI_OK = "ai_ok"                  # AI 可用性探测缓存
KEY_PROFILE_PERSON = "profile_person"   # 人物详情页当前人物 id
KEY_PROFILE_RETURN = "profile_return"   # 人物详情页返回页
KEY_GPS_DISABLED = "gps_disabled"       # GPS 组件开关（AppTest 绕过 v2 组件用）


def init_session():
    defaults = {
        KEY_PAGE: Page.HOME,
        KEY_TRAVEL: None,
        KEY_GROUP_POOL: [],
        KEY_SOLO_MSGS: {},
        KEY_SOLO_PERSON: None,
        KEY_SOLO_CONVO: None,
        KEY_GROUP_MSGS: [],
        KEY_GROUP_MEMBERS: [],
        KEY_GROUP_OPENED: False,
        KEY_GROUP_CONVO: None,
        KEY_AI_OK: None,
        KEY_PROFILE_PERSON: None,
        KEY_PROFILE_RETURN: Page.HOME,
        KEY_GPS_DISABLED: False,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def goto(page: Page):
    """仅切换页面；调用方决定是否 st.rerun()。"""
    st.session_state[KEY_PAGE] = page


def current_page() -> Page:
    return st.session_state[KEY_PAGE]


def travel() -> dict | None:
    return st.session_state.get(KEY_TRAVEL)


def start_travel(query: str, city: str, place_ids: list[str]) -> dict:
    """开启一条新的文旅链路（地点检索完成后调用）。"""
    t = {
        "step": 1,
        "query": query,
        "city": city,
        "place_ids": place_ids,
        "candidate_people": [],   # [{person..., matched_entries}]
        "person_ids": [],
        "preferences": [],
        "notes": "",
        "mode": "dual",
        "days_choice": None,
        "route": None,
        "site_idx": 0,
        "dialog_site": None,      # 当前对话所属站点下标（检测站点切换）
        "site_dialog": [],
        "site_unlocked": [],
        "photo_path": None,
        "journal": "",
        "trip_id": None,
    }
    st.session_state[KEY_TRAVEL] = t
    return t


def reset_travel():
    st.session_state[KEY_TRAVEL] = None


def guard(*need_keys: str) -> bool:
    """下游页前置守卫：travel 存在且 need_keys 均有值，否则回首页。"""
    t = travel()
    if t is None:
        st.info("旅程尚未开始，先回首页挑一处故地吧。")
        goto(Page.HOME)
        return False
    for k in need_keys:
        if t.get(k) in (None, []):
            st.info("缺少前置步骤的数据，请按流程重新开始。")
            goto(Page.HOME)
            return False
    return True


def route_sites(t: dict) -> list[dict]:
    return t["route"]["sites"] if t.get("route") else []


def unlocked_count(t: dict) -> int:
    return sum(1 for v in t.get("site_unlocked", []) if v)
