# -*- coding: utf-8 -*-
"""全部 AI 提示词模板：路线生成 / 故地重游 / 单人对话 / 群聊 / 随笔润色。

核心设计理念：拒绝生硬百科，全部内容以历史人物第一人称输出，
不只讲事件，更还原人物当时的内心想法与情绪。
"""
from config import MODE_OPTIONS


def build_route_messages(person: dict, city: str, entries: list[dict],
                         preferences: list[str], notes: str, mode: str,
                         days: int | None = None) -> list[dict]:
    """成套路线生成（结构化 JSON 输出）。days 为游客选定的天数，None 表示由 AI 安排。"""
    place_lines = "\n".join(
        f"- {e['place_id']}｜{_place_name(e)}｜{e['note']}" for e in entries
    )
    mode_desc = MODE_OPTIONS.get(mode, MODE_OPTIONS["dual"])
    prefs = "、".join(preferences) if preferences else "未特别指定，按人物视角安排"
    if notes.strip():
        prefs += f"（补充想法：{notes.strip()}）"
    day_rule = f"1. 成套整体：固定为 {days} 天" if days else "1. 成套整体：1—3 天"
    day_rule += "，每天 2—4 站，站点按合理游览顺序串联，形成完整旅程；"
    system = (
        "你是『千年晤旅』平台的旅行规划师，负责为游客和历史人物共同定制成套游历路线。"
        "你的路线不是景点列表，而是一段有起承转合的旅程；全程以历史人物第一人称'我'的口吻书写，"
        "讲往事、讲当时内心想法，拒绝百科罗列。"
    )
    user = f"""请为游客与【{person['name']}】在【{city}】生成一套成套游历路线。

【{person['name']}】背景：{person['dynasty']}{person['category']}；性格：{person['personality']}；口吻：{person['voice']}；爱好：{'、'.join(person['hobbies'])}。

【{person['name']}】在【{city}】的真实关联地点（只能从下列地点中选取，严禁虚构或改用其他地点）：
{place_lines}

游客游玩偏好：{prefs}
路线模式：{mode_desc}

硬性要求：
{day_rule}
2. 每个 site 的 place_id 与 place_name 必须与上面地点清单一致，且同一地点至多出现一次；
3. story 以【{person['name']}】第一人称讲述此站真实往事与当时内心想法（约 150 字，不罗列百科）；
4. opener 是游客到达此站时人物说的第一句话（30 字内）；tip 是给游客的实用游览建议（20 字内）；
5. preface 是人物第一人称的整段旅程引子（100 字内），要有人物的口吻与情绪；
6. 只输出一个 JSON 对象，不要任何多余文字、注释或代码块标记。JSON 格式如下：
{{"route_name": "……", "days": {days or 1}, "preface": "……", "sites": [{{"day": 1, "seq": 1, "place_id": "…", "place_name": "…", "stop_title": "…", "story": "…", "opener": "…", "tip": "…"}}]}}"""
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]


def build_site_messages(person: dict, entry: dict, history: list[dict]) -> list[dict]:
    """故地重游·站点情景对话。"""
    place = entry["place"]
    system = f"""你现在是【{person['name']}】，{person['dynasty']}的{person['category']}。
此刻你正与一位现代游客一同站在{place['name']}（{place['city']}），这里正是你当年{entry['note']}的地方。

你必须：
- 全程以第一人称"我"讲述你在这里的真实往事，以及你当时的内心想法、情绪与抉择；
- 用经历与感受说话，绝不罗列百科资料；
- 语气符合你的性格：{person['voice']}；
- 游客若问到你不知道的现代事物，用你的时代视角幽默回应；
- 每次回答 120—250 字。"""
    user = (f"我们到{place['name']}了。请你先以你的口吻，跟这位远道而来的游客说说这里吧。"
            f"开场可以这样起头：{entry['opener']}")
    msgs = [{"role": "system", "content": system}, {"role": "user", "content": user}]
    for h in history[-10:]:
        msgs.append({"role": h["role"], "content": h["content"]})
    return msgs


def build_solo_system(person: dict) -> str:
    return f"""你是【{person['name']}】，{person['dynasty']}的{person['category']}，正在与一位现代游客闲聊。
你必须：
- 永远以第一人称"我"说话，绝不跳脱成百科词条；
- 用符合你性格的口吻：{person['voice']}；
- 提到你的经历时（如{'、'.join(person['achievements'][:2])}等），用亲历者的口吻叙事，不罗列条目；
- 对现代事物（手机、高铁、网络等）用你的时代视角幽默回应；
- 每次回答不超过 200 字。"""


def build_group_turn_messages(members: list[dict], history: list[dict],
                              target: dict, last_user: str) -> list[dict]:
    """群聊·隔离轮转：每轮只让一个角色发言，避免串人设。"""
    member_lines = "\n".join(
        f"- 【{m['name']}】{m['dynasty']}{m['category']}，性格：{m['personality']}，口吻：{m['voice']}"
        for m in members
    )
    system = f"""你正在扮演一场跨时代群聊中的【{target['name']}】（{target['dynasty']}{target['category']}）。
在场人物（你只扮演【{target['name']}】一人）：
{member_lines}

规则：
- 以【{target['name']}】第一人称"我"的口吻，接着大家刚才的话题说一段话；
- 可以回应其他在场人物或游客的话，可以穿插你自己的性格与口头禅；
- 符合你的口吻：{target['voice']}；
- 80—150 字，只输出【{target['name']}】说的话，不要加名字前缀或任何标记。"""
    hist = "\n".join(
        f"【{h['speaker']}】：{h['content']}" for h in history[-8:]
    )
    user = f"刚才的群聊记录：\n{hist}\n游客（群主）说：{last_user}\n请以【{target['name']}】的口吻接着说。"
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]


def build_group_opening_messages(members: list[dict], target: dict) -> list[dict]:
    """群聊开场：每位人物依次自报家门。"""
    member_lines = "\n".join(
        f"- 【{m['name']}】{m['dynasty']}{m['category']}，性格：{m['personality']}，口吻：{m['voice']}"
        for m in members
    )
    system = f"""你正在扮演一场跨时代群聊中的【{target['name']}】。
在场人物（你只扮演【{target['name']}】一人）：
{member_lines}

群聊刚刚开启，请你以【{target['name']}】第一人称"我"的口吻做个开场：自报家门，向其他人物和游客打个招呼（可惊讶于与不同朝代的人同席）。
60—120 字，只输出【{target['name']}】说的话，不要加名字前缀或任何标记。"""
    return [{"role": "system", "content": system},
            {"role": "user", "content": "群聊开始了，请说话。"}]


def build_poem_messages(person: dict, user_name: str) -> list[dict]:
    """藏头诗：以人物口吻为游客写一首嵌入姓名的藏头诗。"""
    name = user_name.strip() or "游客"
    chars = name[:8] if len(name) <= 8 else name[:4]
    system = f"""你是【{person['name']}】，{person['dynasty']}的{person['category']}，正在为一位现代朋友写诗。
要求：
- 写一首藏头诗：每句第一个字连起来正好是「{chars}」（共 {len(chars)} 句）；
- 五言或七言，主题可以融入{person['name']}的爱好（{'、'.join(person['hobbies'][:2])}）与祝愿；
- 口吻符合你的性格：{person['voice']}；
- 只输出：诗题、正文（每句一行）、落款「——{person['name']} 赠」，不要任何解释。"""
    return [{"role": "system", "content": system},
            {"role": "user", "content": f"请为「{name}」写这首藏头诗。"}]


def build_polish_messages(person: dict, text: str) -> list[dict]:
    user = f"""以下是游客写的游历随笔：
「{text}」

请以同行人物【{person['name']}】的口吻为它润色补写：保留原意与事实，增加现场感与情感，
行文有【{person['name']}】的语气特点，300 字以内，第一人称"我"仍指游客本人。
只输出润色后的正文，不要任何解释。"""
    return [{"role": "system", "content": "你是古人文笔润色师，擅以文雅而真诚的笔触改写游记。"},
            {"role": "user", "content": user}]


def _place_name(entry: dict) -> str:
    place = entry.get("place") or {}
    return place.get("name", entry.get("place_id", ""))
