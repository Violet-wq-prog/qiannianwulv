# -*- coding: utf-8 -*-
"""故地重游·情景对话：人物以重游故土视角第一人称讲述，完成对话后解锁打卡。

对话历史存 travel["site_dialog"]；人物开场白（opener）作为第一帧，
营造"到达此站"的沉浸感。用户发言达到 UNLOCK_MIN_TURNS 轮后可解锁打卡。
"""
import streamlit as st

from config import UNLOCK_MIN_TURNS, Page
from core import database, state
from core.ai_client import ai_available, chat_stream
from core.asr import render_audio_input
from core.data_loader import enrich_entries, get_person, get_place, person_entries_in_city
from core.prompt_templates import build_site_messages
from core.scripts import offline_site_reply
from views.common import button_row, goto, render_speaker, scroll_to_bottom, stamp_html, stream_or_fallback


def render():
    if not state.guard("route", "site_unlocked"):
        st.rerun()
        return
    t = state.travel()
    route = t["route"]
    i = t.get("site_idx", 0)
    if i >= len(route["sites"]):
        i = 0
        t["site_idx"] = 0
    site = route["sites"][i]
    person = get_person(route["person_ids"][0])
    place = get_place(site["place_id"])

    # 站点切换时重置对话，以人物开场白开场
    if t.get("dialog_site") != i:
        t["dialog_site"] = i
        t["site_dialog"] = [{"role": "assistant", "content": site["opener"]}]

    st.markdown(f"## 🏮 故地重游 · 第{site['day']}天第{site['seq']}站")
    st.markdown(f"**{site['place_name']}**（{route['city']}）· 同行：{person['name']} · "
                f"{'✅ 已打卡' if t['site_unlocked'][i] else '🔒 未打卡'}")
    if place:
        st.markdown('<div class="qn-quote">' + place["intro"] + "</div>", unsafe_allow_html=True)

    # 对话区
    for m in t["site_dialog"]:
        avatar = "🎭" if m["role"] == "assistant" else None
        with st.chat_message(m["role"], avatar=avatar):
            st.write(m["content"])
    scroll_to_bottom()

    _last = t["site_dialog"][-1] if t["site_dialog"] else None
    if _last and _last["role"] == "assistant":
        render_speaker(_last["content"], person["id"])

    user_turns = sum(1 for m in t["site_dialog"] if m["role"] == "user")
    can_unlock = user_turns >= UNLOCK_MIN_TURNS and not t["site_unlocked"][i]

    render_audio_input()
    prompt = st.chat_input(f"问问{person['name']}当年的心事……", key="site_input")
    if not prompt:
        prompt = st.session_state.pop("asr_pending", None)  # 语音识别结果自动作为消息发送
    if prompt:
        t["site_dialog"].append({"role": "user", "content": prompt})
        entry = _find_entry(person, t["city"], site["place_id"])
        # AI 在线：流式逐字浮现；离线/失败：空流降级离线应答，对话不中断
        stream = None
        if ai_available() and entry:
            stream = chat_stream(build_site_messages(person, entry, t["site_dialog"]))
        fallback = (offline_site_reply(person, entry, prompt) if entry
                    else f"（{person['name']}望着此处出神）这地方的故事，容我慢慢说与你听。")
        reply = stream_or_fallback(stream, fallback)
        t["site_dialog"].append({"role": "assistant", "content": reply})
        st.rerun()

    st.markdown("---")
    if can_unlock:
        st.button("✅ 完成对话 · 解锁打卡", type="primary", key="site_unlock",
                  on_click=lambda: _unlock_site(t, i, site))
    specs = [{"label": "← 返回路线总览", "key": "site_back",
              "on_click": lambda: goto(Page.ROUTE_VIEW)}]
    if t["site_unlocked"][i]:
        nxt = _next_unvisited(t)
        if nxt is not None:
            specs.append({"label": "下一站 →", "key": "site_next", "type": "primary",
                          "on_click": lambda: _go_next(t, nxt)})
        else:
            specs.append({"label": "📸 去同游合影", "key": "site_photo", "type": "primary",
                          "on_click": lambda: goto(Page.PHOTO)})
        button_row(specs)
        st.markdown('<div style="margin-top:.35rem">' + stamp_html("此站已游") + "</div>",
                    unsafe_allow_html=True)
    else:
        button_row(specs)
        st.caption(f"再与{person['name']}聊 {UNLOCK_MIN_TURNS - user_turns} 轮即可解锁打卡")


def _find_entry(person: dict, city: str, place_id: str) -> dict | None:
    for e in enrich_entries(person_entries_in_city(person, city)):
        if e["place_id"] == place_id:
            return e
    return None


def _next_unvisited(t: dict) -> int | None:
    for j, done in enumerate(t["site_unlocked"]):
        if not done:
            return j
    return None


def _unlock_site(t: dict, i: int, site: dict):
    t["site_unlocked"][i] = True
    database.add_checkin(
        t["trip_id"], site["place_id"], site["place_name"],
        site["seq"], t["site_dialog"])
    st.toast("打卡成功！地图上已点亮这一站。")
    st.rerun()


def _go_next(t: dict, nxt: int):
    t["site_idx"] = nxt
    st.rerun()
