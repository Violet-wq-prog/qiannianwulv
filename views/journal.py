# -*- coding: utf-8 -*-
"""游历随笔：写下感悟（可选 AI 以人物口吻润色），与合影一同绑定旅程存档。"""
import streamlit as st
from pathlib import Path

from config import PHOTO_DIR, Page
from core import database, state
from core.ai_client import ai_available, ai_enabled, chat
from core.data_loader import build_index, get_person
from core.photo_utils import make_ticket
from core.prompt_templates import build_polish_messages
from views.common import goto


@st.cache_data(show_spinner=False)
def _ticket_bytes(path: str) -> bytes:
    """票根下载字节缓存：文件每次 rerun 不再重复读盘 + base64 重传。"""
    try:
        return Path(path).read_bytes()
    except OSError:
        return b""


@st.cache_data(ttl=24 * 3600, show_spinner=False)
def _share_bytes(route_json: str, person_id: str, trip_id: int, created_at: str) -> bytes:
    """分享卡片字节缓存。失败 raise 不缓存。"""
    from core.export import export_bytes
    data = export_bytes("share_card", route_json, person_id, trip_id, created_at)
    if not data:
        raise RuntimeError("分享卡片生成失败")
    return data


def _share_card_button(t: dict, route: dict, person: dict):
    import json
    trip_id = t.get("trip_id")
    trip_row = database.get_trip(trip_id)
    try:
        card = _share_bytes(json.dumps(route, ensure_ascii=False, sort_keys=True),
                            person["id"], trip_id, trip_row["created_at"])
        st.download_button("⬇ 分享卡片（含二维码）", card, file_name="分享卡片.png",
                           mime="image/png", key="share_card_download")
    except (RuntimeError, TypeError):
        st.caption("分享卡片生成失败，稍后再试。")


@st.cache_data(ttl=60 * 60 * 24, show_spinner=False)
def _cached_polish(person_id: str, text: str) -> str:
    """随笔润色确定性缓存：同人物 + 同原文不重复付费。失败 raise 不缓存。"""
    if not ai_enabled():
        raise RuntimeError("AI 不可用，跳过缓存")
    person = build_index()["people_by_id"][person_id]
    polished = chat(build_polish_messages(person, text))
    if not polished:
        raise RuntimeError("润色失败，跳过缓存")
    return polished


def render():
    if not state.guard("route"):
        st.rerun()
        return
    t = state.travel()
    route = t["route"]
    person = get_person(route["person_ids"][0])

    st.markdown("## 📝 写下游历随笔")
    st.caption("这一路的故事，值得记下来。可以请" + person["name"] + "替你润色补写。")

    draft_key = "journal_draft"
    text = st.text_area(
        "游历感悟",
        value=st.session_state.get(draft_key, t.get("journal", "")),
        height=220,
        key="journal_text",
        placeholder="例：站在苏堤上，忽然懂了什么叫'欲把西湖比西子'……",
    )
    st.session_state[draft_key] = text

    b1, b2 = st.columns([1.6, 1.4])
    with b1:
        if st.button(f"🖋 请{person['name']}润色", key="journal_polish",
                     disabled=not text.strip()):
            if ai_available():
                with st.spinner(f"{person['name']}正在提笔润色……"):
                    polished = None
                    try:
                        polished = _cached_polish(person["id"], text)
                    except RuntimeError:
                        polished = None
                if polished:
                    st.session_state[draft_key] = polished
                    st.rerun()
                else:
                    st.warning("AI 暂不可用，可直接保存原文。")
            else:
                st.warning("当前为离线演示模式，可直接保存原文。")
    with b2:
        if st.button("💾 保存随笔", type="primary", key="journal_save",
                     disabled=not text.strip()):
            database.add_journal(t["trip_id"], text)
            t["journal"] = text
            st.toast("随笔已存入游历档案！")
            st.rerun()

    rows = database.get_journals(t["trip_id"]) if t.get("trip_id") else []
    if rows:
        st.markdown("#### 已存的随笔")
        for r in rows:
            with st.container(border=True):
                st.write(r["content"])
                st.caption(r["created_at"])

    # —— 年轻化玩法：时空票根 ——
    st.markdown("#### 🎫 时空票根")
    st.caption("旅程结束后生成一张古风纪念票根，把这段时光收藏起来。")
    photos = database.get_photos(t["trip_id"])  # 一次查询复用（原为两次重复连接）
    ticket_rows = [r for r in photos if r["site_key"] == "ticket"]
    if ticket_rows:
        path = PHOTO_DIR / ticket_rows[0]["file_path"]
        if path.exists():
            st.image(str(path), width=330)
            b1, b2 = st.columns(2)
            with b1:
                data = _ticket_bytes(str(path))
                if data:
                    st.download_button("⬇ 下载票根", data, file_name="时空票根.png",
                                       mime="image/png", key="ticket_download")
            with b2:
                _share_card_button(t, route, person)
    elif t.get("trip_id"):
        if st.button("🎫 生成时空票根", key="ticket_gen"):
            with st.spinner("正在制票……"):
                trip_row = database.get_trip(t["trip_id"])
                name = f"ticket_trip{t['trip_id']}.png"
                make_ticket(t["route"], person, t["trip_id"], trip_row["created_at"],
                            PHOTO_DIR / name)
                database.add_photo(t["trip_id"], "ticket", name)
                st.toast("票根已生成，存入游历档案！")
                st.rerun()
        _share_card_button(t, route, person)

    st.markdown("---")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("← 返回路线总览", key="journal_back"):
            goto(Page.ROUTE_VIEW)
    with c2:
        if st.button("🏮 完成旅程 · 收入档案", type="primary", key="journal_finish"):
            if t.get("trip_id"):
                database.complete_trip(t["trip_id"])
            st.toast("整段旅程已存入个人游历档案！")
            goto(Page.ARCHIVE)
