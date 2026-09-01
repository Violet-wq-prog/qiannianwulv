# -*- coding: utf-8 -*-
"""入口B：单人沉浸式对话——人物第一人称讲述生平、遭遇与时代故事。

对话历史按人物隔离存 session（solo_msgs[person_id]），并落库可回查。
AI 不可用时降级到内置应答脚本，聊天不中断。
"""
import streamlit as st

from config import Page
from core import database, state
from core.ai_client import ai_available, ai_enabled, chat, chat_stream
from core.asr import render_audio_input
from core.data_loader import PEOPLE, build_index, get_person, search_people
from core.prompt_templates import build_poem_messages, build_solo_system
from core.scripts import offline_poem, offline_solo_reply
from views.common import goto, person_avatar, render_speaker, scroll_to_bottom, stream_or_fallback


@st.cache_data(ttl=60 * 60 * 24, show_spinner=False)
def _cached_poem(person_id: str, user_name: str) -> str:
    """藏头诗确定性缓存：同人物 + 同姓名不重复付费。失败 raise 不缓存。"""
    if not ai_enabled():
        raise RuntimeError("AI 不可用，跳过缓存")
    person = build_index()["people_by_id"][person_id]
    poem = chat(build_poem_messages(person, user_name), temperature=0.95)
    if not poem:
        raise RuntimeError("藏头诗生成失败，跳过缓存")
    return poem


def render():
    st.markdown("## 💬 与古人闲谈")

    # 人物选择
    col1, col2 = st.columns([2, 1])
    with col1:
        kw = st.text_input("搜索人物（姓名/朝代/身份/事迹）", key="solo_search")
    with col2:
        if st.button("清空重聊", key="solo_reset"):
            pid = st.session_state.get(state.KEY_SOLO_PERSON)
            if pid:
                st.session_state[state.KEY_SOLO_MSGS].pop(pid, None)
                st.session_state[state.KEY_SOLO_CONVO] = None
            st.rerun()

    pool = search_people(kw) if kw.strip() else PEOPLE
    if not pool:
        st.warning("未找到相关人物。试试：苏轼、李白、诸葛亮、发明家、唐代……")
        return
    names = {p["id"]: f"{p['name']} · {p['dynasty']}{p['category']}" for p in pool}
    current = st.session_state.get(state.KEY_SOLO_PERSON)
    if current not in names:
        current = next(iter(names))
    chosen = st.selectbox("选择交谈对象", options=list(names.keys()),
                          format_func=lambda i: names[i],
                          index=list(names.keys()).index(current), key="solo_pick")
    if chosen != st.session_state.get(state.KEY_SOLO_PERSON):
        st.session_state[state.KEY_SOLO_PERSON] = chosen
        st.session_state[state.KEY_SOLO_CONVO] = None
        st.rerun()

    person = get_person(chosen)
    msgs = st.session_state[state.KEY_SOLO_MSGS].setdefault(chosen, [])

    # 开场白
    if not msgs:
        msgs.append({"role": "assistant", "content": person["self_talk"]})

    left, right = st.columns([1, 3])
    with left:
        person_avatar(chosen, width=110)
    with right:
        st.markdown('<div class="qn-quote">' + person["quote"] + "</div>", unsafe_allow_html=True)
        st.caption(f"{person['dynasty']} · {person['category']} · {person['lifespan']}")

    for m in msgs:
        with st.chat_message(m["role"], avatar="🎭" if m["role"] == "assistant" else None):
            st.write(m["content"])
    scroll_to_bottom()

    _last = msgs[-1] if msgs and msgs[-1]["role"] == "assistant" else None
    if _last:
        render_speaker(_last["content"], person["id"])

    render_audio_input()
    prompt = st.chat_input(f"与{person['name']}说点什么……", key="solo_input")
    if not prompt:
        prompt = st.session_state.pop("asr_pending", None)  # 语音识别结果自动作为消息发送
    if prompt:
        msgs.append({"role": "user", "content": prompt})
        # AI 在线：流式逐字浮现；离线/失败：空流降级离线文本，聊天不中断
        stream = None
        if ai_available():
            stream = chat_stream([{"role": "system", "content": build_solo_system(person)}]
                                 + [{"role": m["role"], "content": m["content"]} for m in msgs[-10:]])
        reply = stream_or_fallback(stream, offline_solo_reply(person, prompt))
        msgs.append({"role": "assistant", "content": reply})
        if st.session_state.get(state.KEY_SOLO_CONVO) is None:
            st.session_state[state.KEY_SOLO_CONVO] = database.create_solo_convo(
                chosen, f"与{person['name']}的闲谈")
        database.update_solo_convo(st.session_state[state.KEY_SOLO_CONVO], msgs)
        st.rerun()

    # —— 年轻化玩法：请古人写藏头诗 ——
    with st.expander(f"🎁 请{person['name']}为你写一首藏头诗"):
        pname = st.text_input("你的名字（嵌入诗中）", value="游客", key="poem_name")
        if st.button("求诗", type="primary", key="poem_go", disabled=not pname.strip()):
            with st.spinner(f"{person['name']}正在铺纸研墨……"):
                poem = None
                if ai_available():
                    try:
                        poem = _cached_poem(person["id"], pname.strip())
                    except RuntimeError:
                        poem = None
                if not poem:
                    poem = offline_poem(person, pname.strip())
            msgs.append({"role": "assistant", "content": poem})
            if st.session_state.get(state.KEY_SOLO_CONVO) is None:
                st.session_state[state.KEY_SOLO_CONVO] = database.create_solo_convo(
                    chosen, f"与{person['name']}的闲谈")
            database.update_solo_convo(st.session_state[state.KEY_SOLO_CONVO], msgs)
            st.rerun()

    st.markdown("---")
    st.caption("换人聊天时历史自动保留；点击「清空重聊」可重新开始。")
