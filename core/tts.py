# -*- coding: utf-8 -*-
"""语音朗读：edge-tts（微软 Edge 在线 TTS，免 key）合成 mp3。

失败路径：依赖未装 / 断网 / 微软端点拒绝 → 返回 None，UI 层 caption 友好提示，
任何链路不受影响。合成结果 st.cache_data 缓存（同文本同音色不重复联网合成）。
"""
import asyncio
import io

import streamlit as st

# 音色：男古人默认云希（温润青年），李清照用晓晓（清丽女声）
VOICES = {
    "male": "zh-CN-YunxiNeural",
    "female": "zh-CN-XiaoxiaoNeural",
}
VOICE_BY_PERSON = {
    "li_qingzhao": "female",
}


def tts_ready() -> bool:
    try:
        import edge_tts  # noqa: F401
        return True
    except ImportError:
        return False


def voice_for(person_id: str | None) -> str:
    return VOICES[VOICE_BY_PERSON.get(person_id or "", "male")]


def _synth(text: str, voice: str, buf: io.BytesIO) -> bool:
    """edge-tts 是 async 库；Streamlit 脚本运行在线程中、无事件循环，asyncio.run 安全。
    返回是否成功（失败由调用方降级，异常不缓存）。"""
    try:
        asyncio.get_running_loop()   # 防御：若未来运行在事件循环内则直接降级
        return False
    except RuntimeError:
        pass
    import edge_tts

    async def _run():
        comm = edge_tts.Communicate(text, voice)
        async for chunk in comm.stream():
            if chunk["type"] == "audio":
                buf.write(chunk["data"])

    try:
        asyncio.run(_run())
        return buf.tell() > 0
    except Exception:  # noqa: BLE001 —— 网络/端点拒绝等全部降级
        return False


@st.cache_data(ttl=7 * 24 * 3600, show_spinner=False)
def speech_bytes(text: str, voice: str) -> bytes:
    """合成 mp3（缓存）。失败 raise（异常不进缓存，避免断网冻结缓存）。"""
    buf = io.BytesIO()
    if not _synth(text, voice, buf):
        raise RuntimeError("语音合成失败")
    return buf.getvalue()
