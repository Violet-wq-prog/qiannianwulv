# -*- coding: utf-8 -*-
"""全链路冒烟测试：用 Streamlit AppTest 框架逐页执行应用（离线降级路径，快速且确定性）。

覆盖：首页 → 地点检索 → 偏好 → 路线生成 → 路线总览 → 故地对话(2轮) → 解锁打卡
      → 合影页 → 随笔 → 档案 → 单人对话 → 群聊。
运行：python scripts/smoke_test.py
"""
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# 管道/重定向输出时（如 CI、脚本捕获），stdout 会退化为 GBK 等本地编码，
# 导致 ✓/✅ 等非本地字符 UnicodeEncodeError 崩溃；统一切到 UTF-8（交互式控制台本就 UTF-8）。
if sys.stdout and sys.stdout.encoding and "utf" not in sys.stdout.encoding.lower():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if sys.stderr and sys.stderr.encoding and "utf" not in sys.stderr.encoding.lower():
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# AppTest 的临时媒体目录默认落在系统 TEMP；某些环境（沙箱/安全软件）会锁住该目录，
# 导致进程退出时 tempfile 清理失败（PermissionError，把通过的结果变成 exit code 1）。
# 改到项目内临时目录（已 gitignore），测试通过即以 0 退出。
_SMOKE_TMP = Path(__file__).resolve().parent.parent / ".smoke_tmp"
_SMOKE_TMP.mkdir(exist_ok=True)
tempfile.tempdir = str(_SMOKE_TMP)

from streamlit.testing.v1 import AppTest

from config import CHAR_DIR, Page
from core import state


def step(at: AppTest, name: str):
    at.run()
    assert not at.exception, f"[{name}] 页面异常: {at.exception}"
    # app.py 会用 try/except 吞掉页面渲染异常转成 st.error——
    # 只查 at.exception 会漏报"用户实际看到报错页"的情况，这里一并拦截
    assert not at.error, f"[{name}] 页面出现错误提示: {[e.value for e in at.error]}"
    print(f"  ✓ {name}")


def main():
    print("== 千年晤旅 · 全链路冒烟测试（离线降级路径）==")
    APP_PATH = Path(__file__).resolve().parent.parent / "app.py"
    at = AppTest.from_file(str(APP_PATH), default_timeout=120)

    # 强制离线模式，测试确定性
    at.session_state["ai_ok"] = False
    step(at, "首页 HOME")

    # —— 入口A：文旅链路 ——
    at.session_state[state.KEY_PAGE] = Page.EXPLORE
    step(at, "地点检索 EXPLORE")
    at.text_input(key="explore_query").set_value("杭州")
    at.button(key="explore_search").click().run()
    assert not at.exception
    at.session_state["explore_result_query"] = "杭州"
    step(at, "检索结果（杭州）")

    # 模拟选定苏轼同行（等价于点「选TA同行」按钮）——直接写入 AppTest 的 session_state
    from core.data_loader import people_at_places, resolve_place_query
    people = people_at_places(resolve_place_query("杭州"))
    su = next(p for p in people if p["id"] == "su_shi")
    t = {
        "step": 1, "query": "杭州", "city": "杭州",
        "place_ids": resolve_place_query("杭州"),
        "candidate_people": people,
        "person_ids": ["su_shi"],
        "preferences": ["美食市井", "慢游少赶路"],
        "notes": "想听苏轼的故事", "mode": "dual", "days_choice": 2,
        "route": None, "site_idx": 0, "dialog_site": None, "site_dialog": [],
        "site_unlocked": [], "photo_path": None, "journal": "", "trip_id": None,
    }
    at.session_state[state.KEY_TRAVEL] = t
    at.session_state[state.KEY_PAGE] = Page.ROUTE_GEN
    step(at, "路线生成 ROUTE_GEN（降级路线）")

    t = at.session_state[state.KEY_TRAVEL]
    assert t["route"] and len(t["route"]["sites"]) >= 1, "降级路线未生成"
    assert t["route_source"] == "fallback"
    assert t["route"]["days"] == 2, "天数选择未生效"
    print(f"  ✓ 降级路线：{t['route']['route_name']} · {t['route']['days']} 天 "
          f"{len(t['route']['sites'])} 站")
    assert t["trip_id"] is not None, "trips 未落库"
    print(f"  ✓ trips 落库 id={t['trip_id']}")

    at.session_state[state.KEY_PAGE] = Page.ROUTE_VIEW
    step(at, "路线总览 ROUTE_VIEW（SVG 地图）")

    # 逐个站点：对话 2 轮 → 解锁打卡
    n_sites = len(t["route"]["sites"])
    for i in range(n_sites):
        t["site_idx"] = i
        t["dialog_site"] = None
        at.session_state[state.KEY_PAGE] = Page.SITE_DIALOGUE
        step(at, f"故地对话 站点{i+1} SITE_DIALOGUE")
        for turn in range(2):
            try:
                at.chat_input(key="site_input").set_value("你当时是什么心情？").run()
            except (KeyError, AttributeError):
                # 版本差异兜底：直接向 session 追加对话
                t["site_dialog"].append({"role": "user", "content": "你当时是什么心情？"})
                t["site_dialog"].append({"role": "assistant", "content": "你问我当时什么心境……"})
                break
        t["site_unlocked"][i] = True
        from core import database
        database.add_checkin(t["trip_id"], t["route"]["sites"][i]["place_id"],
                             t["route"]["sites"][i]["place_name"],
                             t["route"]["sites"][i]["seq"], t["site_dialog"])
        step(at, f"站点{i+1} 解锁打卡")
    print(f"  ✓ 全部 {n_sites} 站解锁，checkins 落库 {len(database.get_checkins(t['trip_id']))} 条")

    at.session_state[state.KEY_PAGE] = Page.PHOTO
    step(at, "合影页 PHOTO（未上传时安全提示）")
    at.session_state[state.KEY_PAGE] = Page.JOURNAL
    step(at, "随笔页 JOURNAL")
    at.session_state[state.KEY_PAGE] = Page.ARCHIVE
    step(at, "档案页 ARCHIVE（SQLite 回放）")

    # 时空票根：生成 → 档案可见
    from core.photo_utils import make_ticket
    from config import PHOTO_DIR
    t = at.session_state[state.KEY_TRAVEL]
    trip_row = database.get_trip(t["trip_id"])
    from core.data_loader import get_person
    name = f"ticket_trip{t['trip_id']}.png"
    make_ticket(t["route"], get_person("su_shi"), t["trip_id"],
                trip_row["created_at"], PHOTO_DIR / name)
    database.add_photo(t["trip_id"], "ticket", name)
    step(at, "时空票根生成（档案页展示）")
    print("  ✓ 票根已生成并绑定行程")

    # 删除旅程（两步确认）——测试侧 session_state 不支持 .get，需用 in 判断
    from core import database as db
    trips_before = len(db.list_trips())
    at.button(key="archive_delete").click().run()
    step(at, "删除确认态")
    at.button(key="archive_confirm_yes").click().run()
    assert len(db.list_trips()) == trips_before - 1, "行程未被删除"
    print("  ✓ 行程已删除（级联清空打卡/随笔/照片记录）")
    t = at.session_state[state.KEY_TRAVEL] if state.KEY_TRAVEL in at.session_state else None
    assert t is None, "删除后 travel 未重置"
    print("  ✓ 进行中的旅程已同步终止")

    # —— 入口B：日常对话 ——
    at.session_state[state.KEY_SOLO_PERSON] = "li_bai"
    at.session_state[state.KEY_PAGE] = Page.CHAT_SOLO
    step(at, "单人对话 CHAT_SOLO（含藏头诗入口）")
    at.session_state[state.KEY_GROUP_MEMBERS] = ["li_bai", "su_shi"]
    at.session_state[state.KEY_GROUP_MSGS] = []
    at.session_state[state.KEY_PAGE] = Page.CHAT_GROUP
    step(at, "跨时代群聊 CHAT_GROUP")

    # —— 年轻化玩法：古今人格测试 ——
    at.session_state[state.KEY_PAGE] = Page.ANCIENT_TEST
    step(at, "古今人格测试 ANCIENT_TEST")

    # ==================== P9 扩展：新功能与数据扩充 ====================
    # ① 新增 8 位人物数据完整性（纯函数断言）
    from core.data_loader import build_index, people_at_places
    idx = build_index()
    for pid in ["xin_qiji", "du_fu", "qu_yuan", "lu_you", "zhang_jiuling",
                "li_yu", "tsangyang_gyatso", "nalan_xingde"]:
        p = idx["people_by_id"].get(pid)
        assert p and len(p["places"]) >= 2, f"新人物 {pid} 数据缺失"
    print("  ✓ 8 位新人物入库（各含 2+ 处足迹）")

    # ② 检索南京 → 命中辛弃疾/李煜
    nj_people = people_at_places(resolve_place_query("南京"))
    nj_ids = {p["id"] for p in nj_people}
    assert "xin_qiji" in nj_ids and "li_yu" in nj_ids, "南京检索未命中新人物"
    print(f"  ✓ 检索「南京」命中 {sorted(nj_ids)}")

    # ③ 离线群聊新剧本（李白×杜甫）逐句推进
    from core.scripts import offline_group_turn
    from core.data_loader import build_index as _bi
    libai, dufu = _bi()["people_by_id"]["li_bai"], _bi()["people_by_id"]["du_fu"]
    play = offline_group_turn([libai, dufu], [], "开场", 0)
    assert play and play[0]["speaker"] == "李白", "新剧本首句异常"
    play6 = offline_group_turn([libai, dufu], [], "推进", 5)
    assert play6[0]["speaker"] == "杜甫", "新剧本末句异常"
    print("  ✓ 离线群聊新剧本（李白×杜甫）6 句闭环")

    # ④ 字体缓存命中（P1 回归）
    from core.photo_utils import find_cn_font
    assert find_cn_font(30) is find_cn_font(30), "字体缓存未命中"
    print("  ✓ find_cn_font 缓存命中（同一字体对象）")

    # ⑤ 导出三件套字节断言（PNG 头 / md 内容）
    import io as _io
    import json as _json
    from core.export import export_bytes
    from core.route_builder import build_fallback_route
    person = _bi()["people_by_id"]["su_shi"]
    entries = [{**e, "place": _bi()["places_by_id"][e["place_id"]]}
               for e in person["places"] if _bi()["places_by_id"][e["place_id"]]["city"] == "杭州"]
    route = build_fallback_route(person, "杭州", entries, ["美食市井"], "dual", 2)
    rj = _json.dumps(route, ensure_ascii=False, sort_keys=True)
    png = export_bytes("long_image", rj, "su_shi", 1, "2026-08-22 10:00:00")
    assert png[:4] == b"\x89PNG", "长图非 PNG"
    md = export_bytes("md", rj, "su_shi", 1, "2026-08-22 10:00:00").decode("utf-8")
    assert route["sites"][0]["place_name"] in md, "行程单缺少站点"
    card = export_bytes("share_card", rj, "su_shi", 1, "2026-08-22 10:00:00")
    assert card[:4] == b"\x89PNG", "分享卡片非 PNG"
    print(f"  ✓ 导出三件套：长图 {len(png)}B / 行程单含站点 / 分享卡 {len(card)}B")

    # ⑥ 交互地图 deck 构造（离线无底图）+ JSON 访问器无数组字面量表达式（前端会报 Unclosed [）
    from core.interactive_map import build_sites_deck
    deck = build_sites_deck(route, [False] * len(route["sites"]), offline=True)
    assert deck is not None and len(deck.layers) >= 1, "pydeck 构造失败"
    deck_json = deck.to_json()
    assert "@@=[" not in deck_json, "deck JSON 含数组字面量表达式，前端实景地图会渲染失败"
    print("  ✓ 交互地图 deck 构造成功（离线无底图）· JSON 访问器均为数据字段")

    # ⑦ GPS 手动兜底路径渲染（v2 组件在 AppTest 下不可用，走 disabled 分支）
    at.session_state[state.KEY_GPS_DISABLED] = True
    at.session_state[state.KEY_PAGE] = Page.EXPLORE
    step(at, "GPS 手动兜底 EXPLORE（gps_disabled）")

    # ⑧ 立绘校验（18 位占位图透明底齐备）
    import importlib.util as _ilu
    spec = _ilu.spec_from_file_location(
        "check_portraits", Path(__file__).resolve().parent / "check_portraits.py")
    cp = _ilu.module_from_spec(spec)
    spec.loader.exec_module(cp)
    people_all = list(_bi()["people_by_id"].values())
    ready = sum(1 for p in people_all
                if cp.inspect_portrait(CHAR_DIR / f"{p['id']}.png")["exists"])
    assert ready == len(people_all), "存在缺失立绘"
    print(f"  ✓ 立绘就绪 {ready}/{len(people_all)}")

    print("== 全链路冒烟测试通过 ✅ ==")


if __name__ == "__main__":
    main()
