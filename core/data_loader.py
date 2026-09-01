# -*- coding: utf-8 -*-
"""人物/地点库加载与双向索引构建：地点→人物、人物→地点、城市→地点。"""
from data.people import PEOPLE
from data.places import PLACES, CITY_ALIASES


def _st():
    """惰性导入 streamlit，避免脚本裸跑时刷警告。"""
    import streamlit as st
    return st


def build_index() -> dict:
    """构建全部索引，一次性完成、缓存进 session_state。"""
    people_by_id = {p["id"]: p for p in PEOPLE}
    place_to_people = {}      # place_id -> [person_id]
    person_to_places = {}     # person_id -> [places 条目]
    city_to_places = {}       # city -> [place_id]
    for p in PEOPLE:
        person_to_places[p["id"]] = p.get("places", [])
        for e in p.get("places", []):
            place_to_people.setdefault(e["place_id"], []).append(p["id"])
    for pid, pl in PLACES.items():
        city_to_places.setdefault(pl["city"], []).append(pid)
    return {
        "people_by_id": people_by_id,
        "places_by_id": PLACES,
        "place_to_people": place_to_people,
        "person_to_places": person_to_places,
        "city_to_places": city_to_places,
    }


def get_index() -> dict:
    """取索引（session 缓存）。"""
    st = _st()
    if st.session_state.get("index") is None:
        st.session_state["index"] = build_index()
    return st.session_state["index"]


def get_person(person_id: str) -> dict | None:
    return get_index()["people_by_id"].get(person_id)


def get_place(place_id: str) -> dict | None:
    return get_index()["places_by_id"].get(place_id)


def _normalize_city(query: str) -> str | None:
    """城市别名归一化，如 '钱塘' -> '杭州'。"""
    q = query.strip()
    if not q:
        return None
    if q in CITY_ALIASES:
        return q
    for city, aliases in CITY_ALIASES.items():
        if q in aliases or city in q:
            return city
    return None


def resolve_place_query(query: str) -> list[str]:
    """地点检索：返回匹配的 place_id 列表（按匹配精度排序）。

    优先级：地点名/别名精确命中 → 城市精确命中（该城全部地点）→ 子串匹配。
    """
    q = query.strip()
    if not q:
        return []
    index = get_index()
    exact_places = [
        pid for pid, pl in index["places_by_id"].items()
        if q == pl["name"] or q in pl["aliases"]
    ]
    if exact_places:
        return exact_places
    city = _normalize_city(q)
    if city:
        return index["city_to_places"].get(city, [])
    # 子串兜底
    fuzzy = [
        pid for pid, pl in index["places_by_id"].items()
        if q in pl["name"] or any(q in a for a in pl["aliases"])
    ]
    return fuzzy


def people_at_places(place_ids: list[str]) -> list[dict]:
    """给定地点，返回在此有事迹的人物（去重，附在此地事迹条目列表）。"""
    index = get_index()
    found = {}
    for pid in place_ids:
        for person_id in index["place_to_people"].get(pid, []):
            if person_id not in found:
                found[person_id] = []
            for e in index["person_to_places"][person_id]:
                if e["place_id"] == pid:
                    found[person_id].append(e)
    return [
        {**index["people_by_id"][person_id], "matched_entries": entries}
        for person_id, entries in found.items()
    ]


def person_entries_in_city(person: dict, city: str) -> list[dict]:
    """某人物在某城市的地点事迹条目（供路线生成与检索卡片使用）。"""
    return [
        e for e in person.get("places", [])
        if get_place(e["place_id"]) and get_place(e["place_id"])["city"] == city
    ]


def enrich_entries(entries: list[dict]) -> list[dict]:
    """给人物地点条目附上完整地点对象（place 字段），供 prompt 与视图使用。"""
    return [
        {**e, "place": get_place(e["place_id"])}
        for e in entries
        if get_place(e["place_id"])
    ]


def search_people(keyword: str) -> list[dict]:
    """人物搜索（入口B）：多关键词 AND 匹配姓名/朝代/身份/事迹/爱好/地点等。"""
    index = get_index()
    kws = [k.strip() for k in keyword.replace("，", " ").replace("、", " ").split() if k.strip()]
    if not kws:
        return []
    results = []
    for p in PEOPLE:
        hay = " ".join([
            p["name"], p["dynasty"], p["category"], p["brief"],
            " ".join(p["achievements"]), " ".join(p["hobbies"]), p["quote"],
            " ".join(get_place(e["place_id"])["name"] + get_place(e["place_id"])["city"]
                     for e in p.get("places", []) if get_place(e["place_id"])),
        ])
        if all(k.lower() in hay.lower() for k in kws):
            results.append(p)
    return results
