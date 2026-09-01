# -*- coding: utf-8 -*-
"""个人游历档案：全部行程、地图点亮全景、各站打卡、AI 合影、随笔日记。
数据从 SQLite 重读渲染——浏览器重开、session 丢失后依然可回看。"""
import json

import streamlit as st

from config import PHOTO_DIR, Page
from core import database, state
from core.data_loader import get_person
from core.svg_map import svg_wrap_html
from views.common import goto


@st.cache_data(ttl=24 * 3600, show_spinner=False)
def _archive_export_bytes(kind: str, route_json: str, person_id: str, trip_id: int,
                          created_at: str, checkins_json: str, journals_json: str) -> bytes:
    """档案页导出字节缓存（key 含旅程内容，天然按旅程区分）。失败 raise 不缓存。"""
    from core.export import export_bytes
    data = export_bytes(kind, route_json, person_id, trip_id, created_at,
                        checkins_json, journals_json)
    if not data:
        raise RuntimeError("导出内容为空")
    return data


def _archive_export_row(trip, route: dict, person: dict | None,
                        checkins: list, journals: list):
    if person is None:
        st.caption("同行人物数据缺失，无法导出。")
        return
    route_json = json.dumps(route, ensure_ascii=False, sort_keys=True)
    checkins_json = json.dumps(
        [{"site_key": c["site_key"], "site_name": c["site_name"], "unlocked_at": c["unlocked_at"]}
         for c in checkins], ensure_ascii=False)
    journals_json = json.dumps(
        [{"content": r["content"], "created_at": r["created_at"]} for r in journals],
        ensure_ascii=False)
    try:
        png = _archive_export_bytes("long_image", route_json, person["id"], trip["id"],
                                    trip["created_at"], checkins_json, journals_json)
        md = _archive_export_bytes("md", route_json, person["id"], trip["id"],
                                   trip["created_at"], checkins_json, journals_json)
        card = _archive_export_bytes("share_card", route_json, person["id"], trip["id"],
                                     trip["created_at"], checkins_json, journals_json)
    except RuntimeError:
        st.caption("导出生成失败，稍后再试。")
        return
    c1, c2, c3 = st.columns(3)
    with c1:
        st.download_button("⬇ 路线长图", png, file_name="路线长图.png",
                           mime="image/png", key=f"arch_export_long_{trip['id']}")
    with c2:
        st.download_button("⬇ 行程单", md, file_name="行程单.md",
                           mime="text/markdown", key=f"arch_export_md_{trip['id']}")
    with c3:
        st.download_button("⬇ 分享卡片", card, file_name="分享卡片.png",
                           mime="image/png", key=f"arch_export_card_{trip['id']}")


def render():
    st.markdown("## 📚 我的游历档案")
    trips = database.list_trips()
    if not trips:
        st.info("档案还是空的。去开启一段人文游历吧——路线、打卡、合影、随笔都会收进这里。")
        if st.button("🗺️ 开启一段旅程", type="primary"):
            goto(Page.EXPLORE)
        return

    options = {f"【{t['status'] == 'completed' and '已完成' or '进行中'}】{t['route_name']}"
               f" · {t['created_at']}": t["id"] for t in trips}
    sel_label = st.selectbox("选择一段旅程", options=list(options.keys()), key="archive_select")
    trip = database.get_trip(options[sel_label])

    route = json.loads(trip["route_json"])
    checkins = database.get_checkins(trip["id"])
    unlocked_keys = {c["site_key"] for c in checkins}
    unlocked = [s["place_id"] in unlocked_keys for s in route["sites"]]
    persons = [get_person(pid) for pid in json.loads(trip["person_ids"])]
    person_names = "、".join(p["name"] for p in persons if p)

    st.markdown(f"### {route['route_name']}")
    st.caption(f"地点：{trip['city']} · 同行人物：{person_names} · "
               f"模式：{'人物视角优先' if route['mode']=='person_lead' else '双向融合'} · {trip['created_at']}")
    st.markdown('<div class="qn-quote">' + route["preface"] + "</div>", unsafe_allow_html=True)

    photos = database.get_photos(trip["id"])  # 一次查询复用（指标 + 展示）
    m1, m2, m3 = st.columns(3)
    m1.metric("站点点亮", f"{len(checkins)} / {len(route['sites'])}")
    m2.metric("合影", len(photos))
    m3.metric("随笔", len(database.get_journals(trip["id"])))

    # 地图点亮全景（响应式 SVG，移动端不溢出）
    st.html(svg_wrap_html(route, unlocked))

    st.markdown("#### 各站足迹")
    for i, s in enumerate(route["sites"]):
        with st.container(border=True):
            done = s["place_id"] in unlocked_keys
            st.markdown(f"{'✅' if done else '🔒'} **第{s['day']}天·第{s['seq']}站 · {s['place_name']}**")
            st.caption(s["story"])
            c = next((x for x in checkins if x["site_key"] == s["place_id"]), None)
            if c:
                st.caption(f"打卡时间：{c['unlocked_at']}")

    if photos:
        st.markdown("#### 📸 同游合影与纪念票根")
        cols = st.columns(min(2, len(photos)))
        for col, r in zip(cols, photos):
            path = PHOTO_DIR / r["file_path"]
            if path.exists():
                col.image(str(path), width="stretch")  # 容器宽自适应，手机不溢出
                if r["site_key"] == "ticket":
                    col.caption("🎫 时空票根")

    journals = database.get_journals(trip["id"])
    if journals:
        st.markdown("#### 📝 游历随笔")
        for r in journals:
            with st.container(border=True):
                st.write(r["content"])
                st.caption(r["created_at"])

    # —— 导出与分享 ——
    with st.expander("📤 导出与分享这段旅程"):
        _archive_export_row(trip, route, persons[0], checkins, journals)

    st.markdown("---")
    # —— 删除此段旅程（两步确认，避免误删） ——
    if st.session_state.get("archive_confirming") == trip["id"]:
        st.warning("⚠️ 删除后，这段旅程的路线、打卡记录、合影与随笔都将移除，且不可恢复。")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("确认删除", type="primary", key="archive_confirm_yes"):
                files = database.delete_trip(trip["id"])
                for f in files:                     # 清理合影文件
                    p = PHOTO_DIR / f
                    if p.exists():
                        p.unlink()
                t = state.travel()
                if t and t.get("trip_id") == trip["id"]:
                    state.reset_travel()            # 正在游历的旅程被删则一并终止
                st.session_state.pop("archive_confirming")
                st.toast("该段旅程已从档案中删除。")
                st.rerun()
        with c2:
            if st.button("取消", key="archive_confirm_no"):
                st.session_state.pop("archive_confirming")
                st.rerun()
    else:
        if st.button("🗑 删除此段旅程", key="archive_delete"):
            st.session_state["archive_confirming"] = trip["id"]
            st.rerun()

    b1, b2 = st.columns(2)
    with b1:
        if st.button("← 回首页", key="archive_home"):
            state.reset_travel()
            goto(Page.HOME)
    with b2:
        if st.button("🗺️ 开启新旅程", type="primary", key="archive_new"):
            state.reset_travel()
            goto(Page.EXPLORE)
