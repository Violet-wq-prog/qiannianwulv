# -*- coding: utf-8 -*-
"""AI 统一封装：OpenAI 兼容协议（默认 DeepSeek），带超时/重试/JSON 模式/降级开关。

key 加载链：环境变量 AI_API_KEY → 本项目 .env → 旧项目 server/.env（本机演示兜底）。
设置环境变量 AI_DISABLED=1 可一键进入离线演示模式（全链路降级内容仍可走通）。
"""
import json
import os
import re
import time

from dotenv import dotenv_values

from config import AI_DEFAULT, ENV_PATH, OLD_ENV_PATH


def _read_env_key(path) -> str | None:
    if not path.exists():
        return None
    return dotenv_values(path).get("AI_API_KEY") or None


def get_api_key() -> str:
    key = os.environ.get("AI_API_KEY") or _read_env_key(ENV_PATH) or _read_env_key(OLD_ENV_PATH)
    return (key or "").strip()


def ai_disabled() -> bool:
    return os.environ.get("AI_DISABLED", "0").strip() in ("1", "true", "True")


def ai_available() -> bool:
    """可用性探测（结果缓存进 session）。"""
    import streamlit as st
    if ai_disabled():
        return False
    if st.session_state.get("ai_ok") is None:
        key = get_api_key()
        st.session_state["ai_ok"] = bool(key)
        if not key:
            print("[ai_client] 未找到 AI_API_KEY，进入离线演示模式")
    return bool(st.session_state["ai_ok"])


def ai_enabled() -> bool:
    """纯函数版可用性判断：不碰 session_state，供 st.cache_data 缓存函数内部使用。"""
    return (not ai_disabled()) and bool(get_api_key())


_client = None


def _get_client():
    global _client
    if _client is None:
        from openai import OpenAI
        _client = OpenAI(
            api_key=get_api_key(),
            base_url=os.environ.get("AI_BASE_URL") or AI_DEFAULT["base_url"],
            timeout=AI_DEFAULT["timeout"],
        )
    return _client


def _model() -> str:
    return os.environ.get("AI_MODEL") or AI_DEFAULT["model"]


def chat(messages: list[dict], temperature: float | None = None,
         max_tokens: int | None = None, json_mode: bool = False) -> str | None:
    """单次对话。失败自动重试，最终失败返回 None（由调用方降级）。"""
    if not ai_available():
        return None
    last_err = None
    for attempt in range(AI_DEFAULT["retries"] + 1):
        try:
            kwargs = dict(
                model=_model(),
                messages=messages,
                temperature=temperature if temperature is not None else AI_DEFAULT["temperature_chat"],
                max_tokens=max_tokens or AI_DEFAULT["max_tokens_chat"],
            )
            if json_mode:
                kwargs["response_format"] = {"type": "json_object"}
            resp = _get_client().chat.completions.create(**kwargs)
            content = (resp.choices[0].message.content or "").strip()
            if content:
                return content
        except Exception as e:  # noqa: BLE001 —— 网络/鉴权/限流统一兜底
            last_err = e
            time.sleep(1.5 * (attempt + 1))
    print(f"[ai_client] 调用失败，降级处理：{last_err}")
    return None


def _extract_json(text: str) -> dict | None:
    """宽容解析：剥代码块、截取首尾大括号。"""
    text = re.sub(r"```(?:json)?", "", text).strip()
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end <= start:
        return None
    try:
        return json.loads(text[start:end + 1])
    except json.JSONDecodeError:
        return None


def chat_json(messages: list[dict], temperature: float | None = None,
              max_tokens: int | None = None) -> dict | None:
    """结构化输出。解析失败返回 None（调用方有离线降级），不做二次付费重试。"""
    text = chat(messages, temperature=temperature if temperature is not None else AI_DEFAULT["temperature_route"],
                max_tokens=max_tokens if max_tokens is not None else AI_DEFAULT["max_tokens_route"],
                json_mode=True)
    return _extract_json(text) if text else None


def chat_stream(messages: list[dict], temperature: float | None = None,
                max_tokens: int | None = None):
    """流式对话生成器：逐段 yield 内容增量，供 st.write_stream 渲染"逐字浮现"效果。

    失败路径（鉴权/断网/超时/流中断）：直接结束不 yield，调用方据空流降级离线文本；
    流式中途失败不重试（重放会重复已展示的片段），与 chat() 的整段重试语义分开。
    """
    if not ai_available():
        return
    try:
        resp = _get_client().chat.completions.create(
            model=_model(),
            messages=messages,
            temperature=temperature if temperature is not None else AI_DEFAULT["temperature_chat"],
            max_tokens=max_tokens or AI_DEFAULT["max_tokens_chat"],
            stream=True,
        )
        for chunk in resp:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta
    except Exception as e:  # noqa: BLE001 —— 网络/鉴权/限流统一降级
        print(f"[ai_client] 流式调用中断，降级处理：{e}")
