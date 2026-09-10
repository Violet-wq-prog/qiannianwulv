# -*- coding: utf-8 -*-
"""首页：沉浸式主视觉 + 双入口 + 人物推荐 + 群聊推荐。"""
import streamlit as st

from config import GROUP_RECOMMEND, HOME_RECOMMEND, Page
from core import state
from core.data_loader import get_person
from views.common import goto, person_card_content


def _render_hero() -> None:
    # 浏览器自行选择 WebP；不支持时加载 PNG，不把两张图塞进每次 rerun 消息。
    from html import escape
    base = st.get_option("server.baseUrlPath").strip("/")
    image_root = escape(f"/{base}/app/static" if base else "/app/static", quote=True)
    st.markdown(
        f"""
        <section class="qn-home-hero" aria-label="千年晤旅首页主视觉">
          <picture>
            <source srcset="{image_root}/home_hero_v2.webp" type="image/webp" />
            <img class="qn-home-hero-image" src="{image_root}/home_hero_v2.png" alt="青绿山水画卷、白鹤与临水亭台" fetchpriority="high" />
          </picture>
          <div class="qn-home-copy">
            <div class="qn-home-eyebrow">沉浸式历史人文游历</div>
            <h1 class="qn-home-title">千年晤旅</h1>
            <div class="qn-home-subtitle">与古人同游故地，听亲历者讲往事</div>
            <div class="qn-home-description">输入一座城市，遇见曾在这里生活、游历的人。让山水不再只是风景，让往事重新有了声音。</div>
          </div>
        </section>
        """,
        unsafe_allow_html=True,
    )
    with st.container(key="home_hero_action"):
        if st.button("开启游历  →", key="home_start_travel", type="secondary"):
            goto(Page.EXPLORE)


def render():
    _render_hero()
    st.markdown("## 🏮 千年晤旅 · 沉浸式历史人文游历平台")
    st.markdown('<div class="qn-quote">与史书中走出的故人同游故地——'
                '听他们亲口讲往事，也讲当时没来得及说出口的心事。</div>', unsafe_allow_html=True)

    col_a, col_b = st.columns(2)
    with col_a:
        with st.container(border=True):
            st.markdown("#### 🗺️ 游历 · 故地重游")
            st.caption("地点检索 → 选一位同行古人 → 生成成套路线 → 逐站对话 → 打卡点亮 → 同游合影 → 随笔存档")
            if st.button("开启一场人文游历", type="primary", key="home_start_travel_card"):
                goto(Page.EXPLORE)
    with col_b:
        with st.container(border=True):
            st.markdown("#### 💬 闲谈 · 日常对话")
            st.caption("搜索或推荐历史人物，单人畅谈，或拉几位不同朝代的古人开一场跨时代群聊")
            c1, c2 = st.columns(2)
            with c1:
                if st.button("与古人单人畅谈", key="home_solo"):
                    goto(Page.CHAT_SOLO)
            with c2:
                if st.button("开跨时代群聊", key="home_group"):
                    goto(Page.CHAT_GROUP)

    st.markdown("---")
    st.markdown("#### 🎯 年轻化玩法")
    c1, c2, c3 = st.columns(3)
    with c1:
        with st.container(border=True):
            st.markdown("**🎯 古今人格测试**")
            st.caption("六道题，测测千年前的你是哪位古人")
            if st.button("开测", key="home_test"):
                goto(Page.ANCIENT_TEST)
    with c2:
        with st.container(border=True):
            st.markdown("**🎁 古人赠诗**")
            st.caption("与古人聊天时，请TA为你写一首藏头诗")
            if st.button("去求诗", key="home_poem"):
                st.session_state[state.KEY_SOLO_PERSON] = "su_shi"
                goto(Page.CHAT_SOLO)
    with c3:
        with st.container(border=True):
            st.markdown("**🎫 时空票根**")
            st.caption("旅程结束后生成古风纪念票根，收藏这段时光")
            if st.button("去游历", key="home_ticket"):
                goto(Page.EXPLORE)

    st.markdown("---")
    st.markdown("#### 📜 人物推荐")
    _recommendations(HOME_RECOMMEND[:1])
    with st.expander("查看更多 · 全部人物"):
        _recommendations(HOME_RECOMMEND[1:])

    st.markdown("---")
    st.markdown("#### 🎭 跨时代群聊 · 推荐组合")
    for index, (ids, label) in enumerate(GROUP_RECOMMEND):
        if index % 2 == 0:
            cols = st.columns(2)
        col = cols[index % 2]
        with col:
            with st.container(border=True):
                st.markdown(f"**{label}**")
                names = "、".join(get_person(i)["name"] for i in ids)
                st.caption(names)
                if st.button("开聊", key=f"home_group_{ids[0]}_{ids[1]}"):
                    st.session_state[state.KEY_GROUP_POOL] = list(ids)
                    goto(Page.CHAT_GROUP)

    st.markdown("---")
    st.caption("文旅完整链路：地点检索 → 同行古人 → 偏好融合路线 → 故地重游对话 → 地图点亮 → AI合影 → 游历档案")


def _recommendations(groups):
    for group_name, ids in groups:
        st.markdown(f"**{group_name}**")
        for idx, pid in enumerate(ids):
            if idx % 2 == 0:
                cols = st.columns(2)
            person = get_person(pid)
            with cols[idx % len(cols)], st.container(key=f"person_card_home_{pid}"):
                person_card_content(person)
                if st.button("看小传", key=f"home_profile_{pid}"):
                    st.session_state[state.KEY_PROFILE_PERSON] = pid
                    st.session_state[state.KEY_PROFILE_RETURN] = Page.HOME
                    goto(Page.PERSON_PROFILE)
                if st.button("去聊天", key=f"home_solo_{pid}"):
                    st.session_state[state.KEY_SOLO_PERSON] = pid
                    goto(Page.CHAT_SOLO)
