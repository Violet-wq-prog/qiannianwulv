# -*- coding: utf-8 -*-
"""古今人格测试（年轻化玩法）：MBTI 式趣味问答 → 匹配历史人物 + 专属称号。

规则化打分（不依赖 AI，结果确定可复现）；人物称号用年轻人熟悉的语言，
同时严格对应人物史料性格，不失专业水准。
"""
import streamlit as st

from config import Page
from core import state
from core.data_loader import get_person
from views.common import goto, person_avatar

# 专属称号：年轻化表达 × 史料性格依据
TITLES = {
    "su_shi": ("旷达生活家", "美食、山水、自嘲式幽默——人生再难也要把日子过出滋味。"),
    "li_bai": ("浪漫谪仙人", "酒入豪肠，七分酿成月光——自由是刻进骨子里的浪漫。"),
    "li_qingzhao": ("清醒大女主", "婉约词宗，也是写'生当作人杰'的硬核大女主。"),
    "bi_sheng": ("硬核手艺人", "一介布衣，凭手艺改变世界——工匠精神的极致玩家。"),
    "zhuge_liang": ("靠谱战略家", "隆中对定三分，出师表写孤忠——最稳的队友，没有之一。"),
    "zhang_heng": ("科学狂人", "观星制器两开花，地动仪测千里地震——硬核科研天花板。"),
    "shen_kuo": ("百科全书君", "上知天文下知地理，连磁偏角都被他先发现了。"),
    "wang_wei": ("佛系美学家", "诗中有画，画中有诗——在辋川把生活过成山水画。"),
    "bai_juyi": ("温暖人间客", "写诗要给老妪听懂，修堤要给百姓走——温柔而有力量。"),
    "du_fu": ("忧世担当者", "自己住破茅屋，还想着'大庇天下寒士'——最深的共情者。"),
    "xin_qiji": ("孤勇燃系青年", "五十骑闯五万敌营，栏杆拍遍不改其志——热血从不因岁月降温。"),
    "qu_yuan": ("理想主义斗士", "举世皆浊我独清——为了心里的正道，九死而不悔。"),
    "lu_you": ("长情守护者", "爱一人到八十一岁，念一国到临终遗言——深情与家国皆不辜负。"),
    "zhang_jiuling": ("靠谱大管家", "开元盛世的压舱石，敢在老板面前说真话的温柔君子。"),
    "li_yu": ("内耗艺术家", "把亡国的痛写成千古绝唱——敏感细腻，是天赋也是重负。"),
    "tsangyang_gyatso": ("自由灵魂诗人", "雪域的王与街头的浪子之间，永远选择诗与月光。"),
    "nalan_xingde": ("深情贵公子", "出身顶级豪门，却为情字伤了一生——温柔是最贵的软肋。"),
}

QUESTIONS = [
    ("周末出远门，你最想去？", {
        "去古迹遗址，看历史留下的痕迹": ["su_shi", "li_qingzhao", "zhuge_liang", "du_fu", "li_yu"],
        "去山水之间，露营看云听风": ["li_bai", "wang_wei", "bai_juyi", "tsangyang_gyatso"],
        "去逛博物馆或工坊，研究东西怎么造": ["zhang_heng", "bi_sheng", "shen_kuo"],
        "去边关要塞，感受山河辽阔": ["xin_qiji", "lu_you", "nalan_xingde"],
    }),
    ("遇到重大挫折，你会？", {
        "苦中作乐，把烂牌打出新花样": ["su_shi", "bai_juyi"],
        "仰天大笑出门去，此处不留爷": ["li_bai"],
        "咬紧牙关，把该做的事做完": ["zhuge_liang", "li_qingzhao", "lu_you", "xin_qiji"],
        "冷静复盘，找出问题的'理'": ["shen_kuo", "zhang_heng", "bi_sheng", "zhang_jiuling"],
        "写下来/说给懂的人听，让情绪有个出口": ["du_fu", "li_yu", "nalan_xingde", "tsangyang_gyatso", "qu_yuan"],
    }),
    ("你的创造欲更多在？", {
        "写点什么：诗、文章、歌词": ["su_shi", "li_bai", "li_qingzhao", "wang_wei", "bai_juyi",
                                    "du_fu", "lu_you", "li_yu", "nalan_xingde", "qu_yuan", "tsangyang_gyatso"],
        "造点什么：装置、手作、发明": ["bi_sheng", "zhang_heng"],
        "做成什么：把事办好、把人聚拢": ["zhuge_liang", "shen_kuo", "zhang_jiuling", "xin_qiji"],
    }),
    ("深夜十点，你在？", {
        "对月小酌/听歌emo，思绪飘到天外": ["li_bai", "su_shi", "li_yu", "nalan_xingde", "tsangyang_gyatso"],
        "抬头观星，或刷科普视频": ["zhang_heng", "shen_kuo"],
        "挑灯读书/写日记，复盘今天": ["zhuge_liang", "li_qingzhao", "du_fu", "zhang_jiuling", "qu_yuan"],
        "已经睡了，明天还要精进手艺": ["bi_sheng", "wang_wei"],
        "还没睡：练剑/健身，或琢磨正事": ["xin_qiji", "lu_you"],
    }),
    ("你的表达风格是？", {
        "直球选手，有话就说，情绪拉满": ["li_bai", "xin_qiji", "qu_yuan"],
        "幽默自嘲，再丧也能讲成段子": ["su_shi", "bai_juyi"],
        "含蓄细腻，藏在细节里": ["li_qingzhao", "wang_wei", "li_yu", "nalan_xingde", "tsangyang_gyatso"],
        "少说多做，作品会替我说话": ["bi_sheng", "zhang_heng", "shen_kuo", "zhuge_liang",
                                    "du_fu", "lu_you", "zhang_jiuling"],
    }),
    ("理想的老年生活？", {
        "田园小院，种花喝茶看云": ["wang_wei", "bai_juyi", "zhang_jiuling"],
        "老友常在，酒局诗会不断": ["li_bai", "su_shi", "lu_you"],
        "还在实验室/工坊里折腾": ["zhang_heng", "bi_sheng", "shen_kuo"],
        "儿孙绕膝，家族兴旺": ["zhuge_liang", "li_qingzhao"],
        "写回忆录，把一生的故事留下来": ["du_fu", "li_yu", "nalan_xingde", "tsangyang_gyatso", "qu_yuan"],
    }),
]


def render():
    st.markdown("## 🎯 古今人格测试")
    st.markdown('<div class="qn-quote">六道题，测测千年前的你——是哪位青史留名的古人？</div>',
                unsafe_allow_html=True)

    scores: dict[str, int] = {}
    answers = []
    for i, (q, options) in enumerate(QUESTIONS):
        st.markdown(f"**第 {i + 1} 题 · {q}**")
        choice = st.radio(q, options=list(options.keys()), index=None,
                          key=f"at_q{i}", label_visibility="collapsed")
        answers.append((options, choice))

    if all(c is not None for _, c in answers):
        if st.button("🔮 揭晓我的古代人格", type="primary", key="at_go"):
            for options, choice in answers:
                for pid in options[choice]:
                    scores[pid] = scores.get(pid, 0) + 1
            winner = max(scores, key=scores.get)
            person = get_person(winner)
            title, why = TITLES[winner]
            st.session_state["at_result"] = {"pid": winner, "title": title, "why": why}
            st.rerun()

    res = st.session_state.get("at_result")
    if res:
        person = get_person(res["pid"])
        st.markdown("---")
        left, right = st.columns([1, 2.5])
        with left:
            person_avatar(res["pid"], width=180)
        with right:
            st.markdown(f"### 你的古代人格：{person['name']} · 「{res['title']}」")
            st.markdown(f"**{person['dynasty']}{person['category']}** · 性格：{person['personality']}")
            st.markdown('<div class="qn-quote">' + res["why"] + "</div>", unsafe_allow_html=True)
            st.markdown("**为什么是TA？** 千年前的TA也爱" + "、".join(person["hobbies"]) +
                        "，和你一样——" + person["quote"])
        b1, b2, b3 = st.columns(3)
        with b1:
            if st.button("💬 找TA聊聊", type="primary", key="at_chat"):
                st.session_state[state.KEY_SOLO_PERSON] = res["pid"]
                goto(Page.CHAT_SOLO)
        with b2:
            if st.button("看小传", key="at_profile"):
                st.session_state[state.KEY_PROFILE_PERSON] = res["pid"]
                st.session_state[state.KEY_PROFILE_RETURN] = Page.ANCIENT_TEST
                goto(Page.PERSON_PROFILE)
        with b3:
            if st.button("再测一次", key="at_again"):
                st.session_state.pop("at_result", None)
                st.rerun()
    else:
        st.caption("答完全部六题即可揭晓。测试基于人物库史料性格做规则化匹配，结果稳定可复现。")
