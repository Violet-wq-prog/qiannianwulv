# -*- coding: utf-8 -*-
"""GPS 定位与地理距离：浏览器定位（v2 组件回传）→ 最近故地推荐；失败时手动选城兜底。

说明：浏览器 Geolocation 需要安全上下文（https 或 localhost）。
手机经局域网 http://192.168.x.x 访问时定位必失败 → 自动走手动兜底，属预期行为。
"""
import math

import streamlit as st

from core import state
from core.data_loader import get_place
from data.places import CITY_ALIASES, PLACES

# v2 双向组件：模块级注册一次（多次注册会告警）。
# AppTest 环境无组件管理器时注册可能失败 → _geoloc 置 None，渲染时走手动兜底。
try:
    _geoloc = st.components.v2.component(
        "qn_geoloc",
        html='<div id="qn-gps" style="font-family:KaiTi,serif;color:#3a3226;">📡 正在定位……</div>',
        js="""
        export default function(component) {
          const { setStateValue, parentElement } = component;
          const el = parentElement.querySelector('#qn-gps');
          const say = (t) => { if (el) el.textContent = t; };
          function onOk(p) {
            say('📍 已获取位置');
            setStateValue('gps', {status:'ok', lat:p.coords.latitude, lng:p.coords.longitude});
          }
          function onErr(e) {
            say(e.code === 1 ? '📍 未授权定位，可手动选择城市' : '📍 定位失败，可手动选择城市');
            setStateValue('gps', {status:'err', code:e.code});
          }
          if (!navigator.geolocation) {
            say('📍 浏览器不支持定位，可手动选择城市');
            setStateValue('gps', {status:'unsupported'});
            return;
          }
          navigator.geolocation.getCurrentPosition(onOk, onErr,
            {timeout:8000, maximumAge:300000});
        }
        """,
    )
except Exception:  # noqa: BLE001 —— AppTest 等无组件管理器环境
    _geoloc = None


def haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """球面距离（公里）。"""
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lng2 - lng1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def nearest_places(lat: float, lng: float, top: int = 3) -> list[tuple[str, float]]:
    """距给定坐标最近的故地（place_id, 公里数），升序。"""
    dists = [
        (pid, haversine_km(lat, lng, pl["lat"], pl["lng"]))
        for pid, pl in PLACES.items() if pl.get("lat") is not None
    ]
    dists.sort(key=lambda x: x[1])
    return dists[:top]


def render_gps_block() -> None:
    """定位入口：定位成功显示最近故地 + 公里数；失败/拒绝/不支持 → 手动选城兜底。"""
    if st.session_state.get(state.KEY_GPS_DISABLED):
        _manual_fallback()
        return
    gps = _read_gps()
    if gps and gps.get("status") == "ok":
        try:
            near = nearest_places(float(gps["lat"]), float(gps["lng"]))
        except (TypeError, ValueError):
            near = []
        if near:
            place = get_place(near[0][0])
            st.success(
                f"📍 距你最近的故地：**{place['name']}** · {near[1]:.0f} 公里"
                if place else f"📍 附近找到 {len(near)} 处故地"
            )
            others = "、".join(
                f"{get_place(pid)['name']}（{km:.0f}km）"
                for pid, km in near[1:] if get_place(pid)
            )
            if others:
                st.caption(f"附近还有：{others}")
        _manual_fallback(compact=True)
        return
    _manual_fallback()


def _read_gps() -> dict | None:
    if _geoloc is None:
        return None
    try:
        res = _geoloc(key="qn_gps", height=58)
        if res is None:
            return None
        gps = getattr(res, "gps", None)
        return gps if isinstance(gps, dict) else None
    except Exception:  # noqa: BLE001 —— 组件环境异常时静默走手动兜底
        return None


def _manual_fallback(compact: bool = False):
    """手动选城：计算该城最近故地公里数（供检索参考）。"""
    if not compact:
        st.caption("或手动选择你所在的城市，看看附近有哪些故地。")
    cities = list(CITY_ALIASES)
    city = st.selectbox("你所在的城市", cities, key="gps_city",
                        label_visibility="collapsed" if compact else "visible")
    if city:
        st.caption(f"{city}收录的故地：" + "、".join(
            pl["name"] for pid, pl in PLACES.items() if pl["city"] == city))
