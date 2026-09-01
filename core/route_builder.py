# -*- coding: utf-8 -*-
"""路线数据结构：AI 结果校验补全 + 离线降级路线拼装。

route schema（链路唯一事实源）：
{
  "route_name": str, "days": int, "preface": str,          # 人物第一人称旅程引子
  "mode": str, "city": str, "person_ids": [str],
  "sites": [
    {"day": int, "seq": int, "place_id": str, "place_name": str,
     "stop_title": str, "story": str, "opener": str, "tip": str}
  ]
}
"""
from config import PREF_TYPE_MAP

_TIPS = {
    "古迹": "静观碑刻，细听讲解。",
    "山水": "留半刻，看云听风。",
    "技艺": "细看工序，可动手一试。",
    "市井": "尝一口老味道，和店家聊两句。",
    "博物馆": "带本笔记，慢慢看。",
    "诗词": "对着景致，背一句旧诗。",
}


def _safe_int(v, default: int = 1) -> int:
    """AI 脏数据防御：None/空串/中文数字/浮点字符串一律兜底，绝不抛异常。"""
    if v is None or v == "":
        return default
    if isinstance(v, bool):
        return int(v)
    try:
        return int(float(str(v)))
    except (ValueError, TypeError):
        return default


def normalize_route(raw: dict | None, person: dict, city: str,
                    entries: list[dict], mode: str,
                    days: int | None = None) -> dict | None:
    """AI 输出的校验与补全：过滤非法地点、补齐缺失字段。失败返回 None。

    days 为游客选定的天数：若给出则覆盖 AI 输出并重新分配各站所属天数。
    """
    if not raw or not isinstance(raw, dict) or not raw.get("sites"):
        return None
    by_place_id = {e["place_id"]: e for e in entries}
    by_name = {e["place"]["name"]: e for e in entries}
    sites = []
    for s in raw["sites"]:
        pid = s.get("place_id")
        entry = by_place_id.get(pid) or by_name.get(s.get("place_name", ""))
        if entry is None:      # 严禁虚构地点：不在清单内的一律剔除
            continue
        sites.append({
            "day": max(1, _safe_int(s.get("day"), 1)),
            "seq": _safe_int(s.get("seq"), len(sites) + 1),
            "place_id": entry["place_id"],
            "place_name": entry["place"]["name"],
            "stop_title": s.get("stop_title") or entry["place"]["name"],
            "story": (s.get("story") or entry.get("story") or entry["note"]),
            "opener": s.get("opener") or entry.get("opener") or "来，听我说说这里。",
            "tip": s.get("tip") or _TIPS.get(entry["place"]["type"], "慢慢走，多停留片刻。"),
        })
    if not sites:
        return None
    sites.sort(key=lambda x: (x["day"], x["seq"]))
    if days:
        sites = _assign_days(sites, days)
    else:
        days = max(1, min(3, _safe_int(raw.get("days"), 1)))
    return {
        "route_name": raw.get("route_name") or fallback_route_name(person, city, mode),
        "days": days,
        "preface": raw.get("preface") or _fallback_preface(person, city, entries),
        "mode": mode,
        "city": city,
        "person_ids": [person["id"]],
        "sites": sites,
    }


def build_fallback_route(person: dict, city: str, entries: list[dict],
                         preferences: list[str], mode: str,
                         days: int | None = None) -> dict:
    """离线降级路线：直接由人物库预写文本程序化拼装，保证无 AI 也能成套演示。

    days 为游客选定的天数（1—3），None 时按站点数量自动安排。
    """
    ordered = _order_by_prefs(entries, preferences)
    n = len(ordered)
    days = max(1, min(3, days or 0)) if days else (1 if n <= 3 else (2 if n <= 6 else 3))
    days = min(days, n)  # 天数不超过站点数
    per_day = (n + days - 1) // days
    sites = []
    seq = 1
    for i, e in enumerate(ordered):
        place = e["place"]
        sites.append({
            "day": min(i // per_day + 1, days),
            "seq": seq,
            "place_id": e["place_id"],
            "place_name": place["name"],
            "stop_title": place["name"],
            "story": e.get("story") or e["note"],
            "opener": e.get("opener") or "来，听我说说这里。",
            "tip": _TIPS.get(place["type"], "慢慢走，多停留片刻。"),
        })
        seq += 1
    return {
        "route_name": fallback_route_name(person, city, mode),
        "days": days,
        "preface": _fallback_preface(person, city, entries),
        "mode": mode,
        "city": city,
        "person_ids": [person["id"]],
        "sites": sites,
    }


def _assign_days(sites: list[dict], days: int) -> list[dict]:
    """按 seq 顺序把站点均匀重新分配到 days 天。"""
    days = max(1, min(3, days))
    n = len(sites)
    per_day = (n + days - 1) // days
    for i, s in enumerate(sites):
        s["day"] = min(i // per_day + 1, days)
        s["seq"] = i + 1
    return sites


def fallback_route_name(person: dict, city: str, mode: str) -> str:
    if mode == "person_lead":
        return f"随{person['name']}重走{city}路"
    return f"{person['name']}与我同游{city}"


def _fallback_preface(person: dict, city: str, entries: list[dict]) -> str:
    hobbies = "、".join(person["hobbies"][:2])
    n = len(entries)
    return (f"我是{person['name']}。{city}这方水土，存着我{n}处难忘的旧事，"
            f"也最合我{ hobbies }的性子。今日你我同游，且随我一路慢慢走去——")


def _order_by_prefs(entries: list[dict], preferences: list[str]) -> list[dict]:
    """按用户偏好对站点排序：匹配偏好类型的地点优先（原顺序稳定）。"""
    pref_types = {PREF_TYPE_MAP[p] for p in preferences if p in PREF_TYPE_MAP}
    if not pref_types:
        return list(entries)
    return sorted(
        entries,
        key=lambda e: 0 if e["place"]["type"] in pref_types else 1,
    )
