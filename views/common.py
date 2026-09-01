# -*- coding: utf-8 -*-
"""视图公共小工具：立绘展示、印章 HTML、按钮行、滚动到底。"""
from typing import Iterator

import streamlit as st

from config import CHAR_DIR
from core import state
from core.data_loader import get_person


def person_avatar(person_id: str, width: int = 120, caption: str | None = None):
    """展示人物立绘；占位图缺失时退化为书法名帖样式。"""
    path = CHAR_DIR / f"{person_id}.png"
    if path.exists():
        st.image(str(path), width=width, caption=caption)
    else:
        person = get_person(person_id)
        name = person["name"] if person else person_id
        st.markdown(
            f'<div style="width:{width}px;height:{int(width*1.5)}px;max-width:100%;'
            f'background:linear-gradient(180deg,#e8dcc0,#d9c9a3);border:1px solid #b08d4f;'
            f'border-radius:6px;display:flex;align-items:center;justify-content:center;'
            f'font-family:KaiTi,serif;font-size:{width//4}px;color:#3a3226;'
            f'letter-spacing:0.2em;">{name}</div>',
            unsafe_allow_html=True,
        )


def stamp_html(text: str = "已游") -> str:
    """印章 HTML（唯一实现，样式走 config.py 的 .qn-seal 类）。"""
    return f'<span class="qn-seal">{text}</span>'


def button_row(specs: list[dict]) -> None:
    """按钮行：桌面按 2 列排列，移动端由全局 CSS 断点自动竖排。

    specs: [{"label": str, "key": str, "type": "primary"|"secondary"|None,
             "disabled": bool, "on_click": callable | None}]
    返回被点击按钮的 spec（若有），否则 None。
    """
    for idx, spec in enumerate(specs):
        col_idx = idx % 2
        if col_idx == 0:
            cols = st.columns(2)
        with cols[col_idx]:
            if st.button(spec["label"], key=spec["key"],
                         type=spec.get("type") or "secondary",
                         disabled=spec.get("disabled", False)):
                if spec.get("on_click"):
                    spec["on_click"]()


def scroll_to_bottom() -> None:
    """聊天页渲染后滚动到底部（rerun 后浏览器滚动位置会回到顶部）。"""
    st.html(
        "<script>window.setTimeout(()=>window.scrollTo(0, document.body.scrollHeight), 120)</script>",
        unsafe_allow_javascript=True,
    )


def render_speaker(text: str, person_id: str | None = None) -> None:
    """朗读一段话：expander 内点击才合成（避免每次 rerun 联网合成）。

    edge-tts 未装 / 断网 / 合成失败均 caption 友好提示，不影响任何链路。
    """
    from core.ai_client import ai_disabled
    from core.tts import speech_bytes, tts_ready, voice_for
    if ai_disabled():
        st.caption("🔇 离线演示模式：语音朗读需联网，暂不可用。")
        return
    if not tts_ready():
        st.caption("🔇 语音引擎未安装（pip install edge-tts）。")
        return
    with st.expander("🔊 朗读这段话"):
        try:
            audio = speech_bytes(text[:500], voice_for(person_id))
            st.audio(audio, format="audio/mpeg")
        except RuntimeError:
            st.caption("语音合成暂时失败（需联网），请稍后再试。")


def typewriter(text: str, size: int = 6) -> Iterator[str]:
    """把整段文本切成小块逐段产出，配合 st.write_stream 呈现打字机效果。

    用于群聊等拿到完整回复后仍想保留"逐字浮现"观感的场景。
    """
    for i in range(0, len(text), size):
        yield text[i:i + size]


def stream_or_fallback(stream_iter, fallback_text: str = "") -> str:
    """在 assistant 气泡内流式渲染 AI 回复（st.write_stream，逐字浮现）。

    - stream_iter 为 None 或空流（离线/失败/无 AI）→ 直接写 fallback_text；
    - 返回实际写入的完整文本，供调用方落库/追加历史。
    """
    text = ""
    if stream_iter is not None:
        with st.chat_message("assistant"):
            text = st.write_stream(stream_iter)
    if not text:
        text = fallback_text or ""
        if text:
            with st.chat_message("assistant"):
                st.write(text)
    return text


def goto(page, rerun: bool = True):
    state.goto(page)
    if rerun:
        st.rerun()
