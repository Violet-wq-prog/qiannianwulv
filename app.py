# -*- coding: utf-8 -*-
"""《千年晤旅——沉浸式历史人文游历交互平台》唯一入口。

单入口 + session_state 状态机路由：改 st.session_state.page 即跳页，
文旅链路数据经 travel dict 在各环节闭环流转；SQLite 仅作落盘副本。
运行：streamlit run app.py
离线演示：AI_DISABLED=1 streamlit run app.py（全链路降级内容可走通）
开发说明：本项目由 AI 辅助开发。
"""
import importlib
import streamlit as st

from config import GLOBAL_CSS, Page
from core import database, state
from core.ai_client import ai_available
from core.data_loader import get_index, get_person

st.set_page_config(page_title="千年晤旅 · 沉浸式历史人文游历", page_icon="🏮", layout="wide")
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)

state.init_session()
if not st.session_state.get("db_ready"):
    database.init_db()
    st.session_state["db_ready"] = True
get_index()  # 预热双向索引

# 视图惰性导入：只加载当前页模块（PIL 等重依赖不再拖慢启动）
_VIEW_MODULES = {
    Page.HOME: "home",
    Page.EXPLORE: "explore",
    Page.PERSON_PROFILE: "person_profile",
    Page.PREFERENCE: "preference",
    Page.ROUTE_GEN: "route_gen",
    Page.ROUTE_VIEW: "route_view",
    Page.SITE_DIALOGUE: "site_dialogue",
    Page.PHOTO: "photomontage",
    Page.JOURNAL: "journal",
    Page.ARCHIVE: "archive",
    Page.CHAT_SOLO: "chat_solo",
    Page.CHAT_GROUP: "chat_group",
    Page.ANCIENT_TEST: "ancient_test",
}


def _render_page(page: Page):
    mod = _VIEW_MODULES.get(page, "home")
    importlib.import_module(f"views.{mod}").render()


def _sidebar():
    with st.sidebar:
        st.markdown("## 🏮 千年晤旅")
        st.caption("沉浸式历史人文游历交互平台")
        if ai_available():
            st.markdown('<span style="color:#9ccc8a;font-size:.85rem;">● AI 在线 · DeepSeek</span>',
                        unsafe_allow_html=True)
        else:
            st.markdown('<span style="color:#d9a05b;font-size:.85rem;">● 离线演示模式（内置剧本）</span>',
                        unsafe_allow_html=True)
        st.markdown("---")

        t = state.travel()
        if t and t.get("route"):
            st.markdown("**当前旅程**")
            st.caption(f"{t['route']['route_name']}")
            if t.get("person_ids"):
                p = get_person(t["person_ids"][0])
                if p:
                    st.caption(f"同行：{p['name']} · 点亮 {state.unlocked_count(t)}/"
                               f"{len(t['route']['sites'])} 站")
            st.markdown("---")

        # 导航用无状态按钮：radio 的自身状态会与程序化跳页互相覆盖，导致页面被弹回首页
        nav_items = [(Page.HOME, "🏠 首页"), (Page.EXPLORE, "🗺️ 开启游历"),
                     (Page.CHAT_SOLO, "💬 单人闲谈"), (Page.CHAT_GROUP, "🎭 跨时代群聊"),
                     (Page.ANCIENT_TEST, "🎯 古今人格测试"), (Page.ARCHIVE, "📚 游历档案")]
        current = state.current_page()
        nav_cols = st.columns(2)
        for idx, (pg, label) in enumerate(nav_items):
            with nav_cols[idx % 2]:
                kind = "primary" if pg == current else "secondary"
                if st.button(label, key=f"sidebar_nav_{pg.value}", type=kind,
                             width="stretch"):
                    state.goto(pg)
                    st.rerun()
        st.markdown("---")
        if st.button("🔄 重新开始", key="sidebar_reset"):
            state.reset_travel()
            st.rerun()
        st.caption("地点检索 → 同行古人 → 融合路线\n→ 故地对话 → 打卡 → 合影 → 随笔")


page = state.current_page()
_sidebar()
try:
    _render_page(page)
except Exception as e:  # noqa: BLE001 —— 演示现场兜底，避免白屏
    st.error("页面出错了，可点击侧边栏「重新开始」回到首页。")
    st.caption(f"错误详情（调试用）：{e!r}")
    print(f"[app] 页面 {page} 渲染异常：{e!r}")
