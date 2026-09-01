# -*- coding: utf-8 -*-
"""入口B：跨时代历史人物群聊——多位不同朝代人物互辩互答，思想碰撞。

AI 模式采用"隔离轮转"：每轮只请求一个角色发言（system 含全体设定），避免串人设；
各成员回复并发请求（ThreadPoolExecutor），5 人一轮从 ~3 分钟降到 ~10-20 秒。
开场白为确定性调用，st.cache_data 缓存（同组合不重复付费）。
离线模式降级为预置剧本（李白×苏轼月下对饮、李白×杜甫诗坛双圣、诸葛亮×张衡奇技安邦等）。
"""
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

import streamlit as st

from config import Page
from core import database, state
from core.ai_client import ai_available, ai_enabled, chat
from core.asr import render_audio_input
from core.data_loader import PEOPLE, build_index, get_person
from core.prompt_templates import build_group_opening_messages, build_group_turn_messages
from core.scripts import offline_group_turn
from views.common import goto, render_speaker, scroll_to_bottom, typewriter


def _concurrency() -> int:
    """群聊并发数（环境变量可调，限流时可降到 3 或 1）。"""
    try:
        return max(1, min(5, int(os.environ.get("AI_GROUP_CONCURRENCY", "5"))))
    except ValueError:
        return 5


@st.cache_data(ttl=6 * 60 * 60, show_spinner=False)
def _cached_opening_lines(member_ids: tuple) -> tuple:
    """群聊开场白缓存：同组合不重复付费。返回 ((speaker, content), ...)。

    铁律：不碰 session_state（build_index/ai_enabled 均为纯函数）；失败 raise 不缓存。
    """
    if not ai_enabled():
        raise RuntimeError("AI 不可用，跳过缓存")
    index = build_index()
    persons = [index["people_by_id"][i] for i in member_ids if i in index["people_by_id"]]
    out = []
    for p in persons:
        line = chat(build_group_opening_messages(persons, p))
        if line:
            out.append((p["name"], line))
    return tuple(out)


def render():
    st.markdown("## 🎭 跨时代群聊")
    st.caption("把不同朝代的人物拉进同一场对话——让李白与苏轼对饮，让李白与杜甫论诗。")

    names = {p["id"]: f"{p['name']} · {p['dynasty']}{p['category']}" for p in PEOPLE}
    pool = st.session_state[state.KEY_GROUP_POOL]
    default = [i for i in pool if i in names] or ["li_bai", "su_shi"]

    c1, c2 = st.columns([3, 1])
    with c1:
        members = st.multiselect(
            "选择在场人物（2—5 位）", options=list(names.keys()),
            format_func=lambda i: names[i], default=default, key="group_pick")
    with c2:
        st.markdown("")
        if st.button("🎬 开启群聊", type="primary", key="group_start",
                     disabled=len(members) < 2):
            st.session_state[state.KEY_GROUP_MEMBERS] = members
            st.session_state[state.KEY_GROUP_MSGS] = []
            st.session_state[state.KEY_GROUP_OPENED] = False  # 换组合重置开场守卫
            st.session_state[state.KEY_GROUP_CONVO] = None
            _opening_round(members)
            st.rerun()

    msgs = st.session_state[state.KEY_GROUP_MSGS]
    active = st.session_state[state.KEY_GROUP_MEMBERS]
    if not active:
        st.markdown('<div class="qn-quote">选几位古人，让千年之隔的他们同桌而谈。</div>',
                    unsafe_allow_html=True)
        return
    persons = [get_person(i) for i in active if get_person(i)]

    for m in msgs:
        speaker = m["speaker"]
        is_me = speaker.startswith("游客")
        with st.chat_message("user" if is_me else "assistant",
                             avatar=None if is_me else "🎭"):
            st.markdown(f"**{speaker}**：{m['content']}")
    scroll_to_bottom()

    _last = msgs[-1] if msgs and not msgs[-1]["speaker"].startswith("游客") else None
    if _last:
        last_person = next((p for p in persons if p["name"] == _last["speaker"]), None)
        render_speaker(_last["content"], last_person["id"] if last_person else None)

    render_audio_input()
    prompt = st.chat_input("对在场古人说点什么……", key="group_input")
    if not prompt:
        prompt = st.session_state.pop("asr_pending", None)  # 语音识别结果自动作为消息发送
    if prompt:
        msgs.append({"speaker": f"游客（你）", "content": prompt})
        if ai_available():
            _ai_turns(persons, msgs, prompt)
        else:
            said = sum(1 for m in msgs if not m["speaker"].startswith("游客"))
            for line in offline_group_turn(persons, msgs, prompt, said):
                msgs.append(line)
                with st.chat_message("assistant"):
                    st.write_stream(typewriter(line["content"]))
        if st.session_state.get(state.KEY_GROUP_CONVO) is None:
            st.session_state[state.KEY_GROUP_CONVO] = database.create_group_convo(
                active, " × ".join(p["name"] for p in persons) + " 的跨时代群聊")
        database.update_group_convo(st.session_state[state.KEY_GROUP_CONVO], msgs)
        st.rerun()

    st.markdown("---")
    if st.button("← 回首页", key="group_home"):
        goto(Page.HOME)


def _ai_turns(persons: list[dict], msgs: list, prompt: str):
    """每位成员并发请求一轮回复；完成一个就在主线程渲染一个（打字机渐进浮现），
    不再干等最慢的成员（原 ex.map 需全部完成后才一次性展示）。"""
    def _ask(p):
        return (p["name"], chat(build_group_turn_messages(persons, msgs, p, prompt)))

    with ThreadPoolExecutor(max_workers=min(_concurrency(), len(persons))) as ex:
        futures = [ex.submit(_ask, p) for p in persons]
        for fut in as_completed(futures):
            name, reply = fut.result()
            if not reply:
                continue
            msgs.append({"speaker": name, "content": reply})
            with st.chat_message("assistant"):
                st.write_stream(typewriter(reply))


def _opening_round(members: list[str]):
    """群聊开场：每位人物自报家门（缓存 / AI / 离线剧本首句）。幂等：KEY_GROUP_OPENED 守卫。"""
    if st.session_state.get(state.KEY_GROUP_OPENED):
        return
    st.session_state[state.KEY_GROUP_OPENED] = True
    persons = [get_person(i) for i in members if get_person(i)]
    msgs = st.session_state[state.KEY_GROUP_MSGS]
    if ai_available():
        try:
            lines = _cached_opening_lines(tuple(m["id"] for m in persons))
        except RuntimeError:
            lines = ()
        if lines:
            msgs.extend({"speaker": name, "content": content} for name, content in lines)
            return
        # 缓存不可用（离线/失败）：退回逐位生成，保证有开场
        for p in persons:
            with st.spinner(f"{p['name']}正在打量在座诸位……"):
                line = chat(build_group_opening_messages(persons, p))
            if line:
                msgs.append({"speaker": p["name"], "content": line})
        return
    lines = offline_group_turn(persons, [], "群聊开场", 0)
    msgs.extend(lines)
