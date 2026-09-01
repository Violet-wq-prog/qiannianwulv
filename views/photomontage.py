# -*- coding: utf-8 -*-
"""同游合影：上传自拍 → PIL 合成"我与古人同游"合照 → 绑定点位存档。"""
import logging

import streamlit as st

from config import PHOTO_DIR, Page
from core import database, state
from core.data_loader import get_person
from core.photo_utils import compose_photo
from views.common import goto

logger = logging.getLogger(__name__)


def render():
    if not state.guard("route", "site_unlocked"):
        st.rerun()
        return
    t = state.travel()
    route = t["route"]
    person = get_person(route["person_ids"][0])
    done_idx = [i for i, v in enumerate(t["site_unlocked"]) if v]
    if not done_idx:
        # 提示放在目标页，避免"一闪而过"的提示后立即跳走
        st.session_state["photo_hint"] = "先完成至少一处站点的故地重游对话，再来合影吧。"
        goto(Page.ROUTE_VIEW)
        return

    if st.session_state.get("photo_hint"):
        st.info(st.session_state.pop("photo_hint"))

    st.markdown("## 📸 我与古人同游 · AI 合影")
    st.caption("上传你的旅行自拍，与" + person["name"] + "合成一张古风同游合照，绑定点位存入档案。")

    site_labels = {i: route["sites"][i]["place_name"] for i in done_idx}
    sel = st.selectbox("选择合影点位", options=list(site_labels.keys()),
                       format_func=lambda i: site_labels[i], key="photo_site")

    uploaded = st.file_uploader("上传自拍（jpg/png）", type=["jpg", "jpeg", "png"], key="photo_upload")

    photos = database.get_photos(t["trip_id"]) if t.get("trip_id") else []  # 一次查询复用

    if uploaded is not None and st.button("🖼 生成同游合影", type="primary", key="photo_gen"):
        with st.spinner("正在铺纸研墨，合成合影……"):
            site = route["sites"][sel]
            n = len(photos) + 1
            out_name = f"trip{t['trip_id']}_{person['id']}_{site['place_id']}_{n}.png"
            out_path = PHOTO_DIR / out_name
            try:
                compose_photo(uploaded.getvalue(), person, site["place_name"], out_path)
                database.add_photo(t["trip_id"], site["place_id"], out_name)
                t["photo_path"] = out_name
                st.toast("合影已成！")
                st.rerun()
            except OSError as e:
                # 图片打不开：用户可恢复错误，提示友好原因
                logger.warning("合影合成读取失败：%r", e)
                st.warning("这张图片读不了，换一张清晰的自拍试试？")
            except Exception:  # noqa: BLE001 —— 其余异常不向用户裸透堆栈
                logger.exception("合影合成失败")
                st.error("合影合成失败了，可以稍后重试，或换一张图片。")

    # 已有合影展示
    if photos:
        st.markdown("#### 本次旅程的合影")
        for r in photos:
            path = PHOTO_DIR / r["file_path"]
            if path.exists():
                st.image(str(path), width="stretch")  # 容器宽自适应，手机不溢出
                st.caption(f"绑定点位：{r['site_key']} · {r['created_at']}")

    st.markdown("---")
    b1, b2 = st.columns(2)
    with b1:
        if st.button("← 返回路线总览", key="photo_back"):
            goto(Page.ROUTE_VIEW)
    with b2:
        if st.button("📝 写游历随笔", key="photo_journal"):
            goto(Page.JOURNAL)
