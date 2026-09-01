# -*- coding: utf-8 -*-
"""语音输入：浏览器 Web Speech API（webkitSpeechRecognition）——零 Python 依赖、免 key。

识别在浏览器端完成（Chrome/Edge 原生支持，需联网；国内网络下 Google 识别端点可能失败，
组件内会给出友好提示并回退文字输入）。Firefox/Safari 不支持时组件内提示。
AppTest 等无组件管理器环境 _asr=None，渲染回退为文字输入提示，任何链路不受影响。

未来若接入离线 ASR 模型（funasr / faster-whisper 等），只需替换 transcribe() 实现，
视图层无需改动（接口已保留）。
"""
import streamlit as st

# 语音识别组件：点击按钮 → 浏览器录音 → 本地语音服务识别 → 文本回传 Python。
# 一次性结果（带时间戳 ts）注入 session（asr_pending），视图层自动作为消息发送。
_ASR_HTML = """
<div id="qn-asr" style="font-family:KaiTi,serif;color:#3a3226;margin-bottom:.2rem;">
  🎤 点击下方按钮，说给古人听（Chrome/Edge）
</div>
<button id="qn-asr-btn"
  style="font-family:KaiTi,serif;font-size:1rem;padding:.35rem 1rem;
         background:linear-gradient(180deg,#8c2f24,#a63d2f);color:#fdf6e3;
         border:1px solid #6e241b;border-radius:4px;cursor:pointer;letter-spacing:.1em;">
  🎙️ 点击说话
</button>
"""

_ASR_JS = """
export default function(component) {
  const { setStateValue, parentElement } = component;
  const el = parentElement.querySelector('#qn-asr');
  const btn = parentElement.querySelector('#qn-asr-btn');
  const say = (t) => { if (el) el.textContent = t; };
  const send = (payload) => setStateValue('asr', { ...payload, ts: Date.now() });

  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SR) {
    say('🔇 当前浏览器不支持语音输入，请用文字输入');
    send({ status: 'unsupported' });
    return;
  }
  let rec = null, listening = false;
  function stop() { if (rec) { try { rec.stop(); } catch (e) {} } }
  function start() {
    listening = true;
    btn.textContent = '⏹ 点击结束';
    say('🎙️ 正在聆听……');
    rec = new SR();
    rec.lang = 'zh-CN';
    rec.interimResults = false;
    rec.maxAlternatives = 1;
    rec.onresult = (ev) => {
      const text = (ev.results[0][0].transcript || '').trim();
      say(text ? ('✅ ' + text) : '🔇 没听清，再试一次');
      if (text) send({ status: 'ok', text });
      listening = false;
      btn.textContent = '🎙️ 点击说话';
    };
    rec.onerror = (ev) => {
      const msg = ev.error === 'not-allowed'
        ? '📍 未授权麦克风，请用文字输入'
        : (ev.error === 'network'
           ? '🌐 语音识别服务不可用（需联网），请用文字输入'
           : '🔇 语音识别失败（' + ev.error + '），请用文字输入');
      say(msg);
      send({ status: 'err', error: ev.error });
      listening = false;
      btn.textContent = '🎙️ 点击说话';
    };
    rec.onend = () => { listening = false; btn.textContent = '🎙️ 点击说话'; };
    try { rec.start(); } catch (e) { say('🔇 语音识别启动失败，请用文字输入'); }
  }
  btn.onclick = () => { listening ? stop() : start(); };
}
"""

try:
    _asr = st.components.v2.component("qn_asr", html=_ASR_HTML, js=_ASR_JS)
except Exception:  # noqa: BLE001 —— AppTest 等无组件管理器环境
    _asr = None


def asr_ready() -> bool:
    """语音识别组件是否可用（浏览器支持与否由组件内 JS 判定）。"""
    return _asr is not None


def transcribe(audio: bytes) -> str | None:
    """识别录音为文本（保留接口：未来接入离线模型时替换实现）。"""
    return None


def render_audio_input() -> None:
    """语音输入入口：浏览器端识别 → 文本写入 st.session_state['asr_pending']，
    由各聊天视图自动作为用户消息发送（见 chat_solo / site_dialogue / chat_group）。

    不支持 / 失败 / 组件环境缺失：友好提示回退文字输入，绝不阻断聊天链路。
    """
    if _asr is None:
        st.caption("🎤 语音输入不可用（当前环境不支持），请用下方文字输入。")
        return
    try:
        res = _asr(key="qn_asr", height=118)
    except Exception:  # noqa: BLE001 —— 组件环境异常时静默回退文字输入
        return
    if res is None:
        return
    val = getattr(res, "asr", None)
    if not isinstance(val, dict) or val.get("status") != "ok":
        return
    text = (val.get("text") or "").strip()
    ts = val.get("ts") or 0
    if not text or ts == st.session_state.get("asr_last_ts"):
        return  # 同一次识别结果不重复注入（rerun 幂等）
    st.session_state["asr_last_ts"] = ts
    st.session_state["asr_pending"] = text
    st.success(f"🎤 已听到：{text}")
