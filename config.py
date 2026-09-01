# -*- coding: utf-8 -*-
"""全局配置：页面枚举、路径、偏好选项、AI 参数、古风全局样式。"""
from enum import Enum
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
DATA_DIR = PROJECT_ROOT / "data"
ASSETS_DIR = PROJECT_ROOT / "assets"
CHAR_DIR = ASSETS_DIR / "characters"
BG_DIR = ASSETS_DIR / "backgrounds"
PHOTO_DIR = ASSETS_DIR / "photos"
DB_PATH = DATA_DIR / "qiannian.db"
ENV_PATH = PROJECT_ROOT / ".env"
# 兜底：复用旧项目的 DeepSeek key（本机演示环境）
OLD_ENV_PATH = Path(r"D:\ai-chat-platform\server\.env")

# 字体目录：优先项目内置字体（云端 Linux 无 Windows 字体），本机回退 Windows Fonts
FONTS_DIR = (ASSETS_DIR / "fonts") if (ASSETS_DIR / "fonts").exists() else Path(r"C:\Windows\Fonts")
FONT_CANDIDATES = ["kaiti.ttf", "simkai.ttf", "msyh.ttc", "simhei.ttf", "simsun.ttc", "msyhbd.ttc"]


class Page(str, Enum):
    HOME = "home"                      # 首页（双入口）
    EXPLORE = "explore"                # 入口A·步1：地点检索
    PERSON_PROFILE = "person_profile"  # 人物详情
    PREFERENCE = "preference"          # 入口A·步2：偏好采集
    ROUTE_GEN = "route_gen"            # 路线生成（进页即触发）
    ROUTE_VIEW = "route_view"          # 路线总览（SVG 地图 + 站点卡片）
    SITE_DIALOGUE = "site_dialogue"    # 故地重游对话 + 解锁打卡
    PHOTO = "photo"                    # AI 同游合影
    JOURNAL = "journal"                # 游历随笔
    ARCHIVE = "archive"                # 个人游历档案
    CHAT_SOLO = "chat_solo"            # 入口B：单人对话
    CHAT_GROUP = "chat_group"          # 入口B：跨时代群聊
    ANCIENT_TEST = "ancient_test"      # 年轻化玩法：古今人格测试


PAGE_TITLES = {
    Page.HOME: "首页",
    Page.EXPLORE: "寻访故地",
    Page.PERSON_PROFILE: "人物小传",
    Page.PREFERENCE: "游兴相告",
    Page.ROUTE_GEN: "路线生成",
    Page.ROUTE_VIEW: "游历路线",
    Page.SITE_DIALOGUE: "故地重游",
    Page.PHOTO: "同游合影",
    Page.JOURNAL: "游历随笔",
    Page.ARCHIVE: "游历档案",
    Page.CHAT_SOLO: "与古人闲谈",
    Page.CHAT_GROUP: "跨时代群聊",
    Page.ANCIENT_TEST: "古今人格测试",
}

# 偏好选项：label 与地点类型/主题的匹配关键词
PREF_OPTIONS = ["文化古迹", "美食市井", "山水风景", "慢游少赶路", "博物馆研学", "诗词打卡", "手作体验"]
PREF_TYPE_MAP = {
    "文化古迹": "古迹", "美食市井": "市井", "山水风景": "山水",
    "博物馆研学": "博物馆", "诗词打卡": "诗词", "手作体验": "技艺", "慢游少赶路": "慢游",
}

MODE_OPTIONS = {
    "person_lead": "模式A · 人物视角优先——以古人当年真实行踪与心迹为主轴串联路线",
    "dual": "模式B · 双向融合——你的游玩喜好与古人的生平爱好交融，共同编排行程",
}

# 首页推荐分组
HOME_RECOMMEND = [
    ("课本热点", ["su_shi", "li_bai", "li_qingzhao", "zhuge_liang"]),
    ("诗圣词宗", ["du_fu", "xin_qiji", "qu_yuan", "lu_you"]),
    ("科技之光", ["bi_sheng", "zhang_heng", "shen_kuo"]),
    ("帝王词人", ["li_yu", "nalan_xingde", "tsangyang_gyatso", "zhang_jiuling"]),
    ("诗画风流", ["wang_wei", "bai_juyi"]),
]

# 群聊推荐组合（离线剧本支持的组合优先展示）
GROUP_RECOMMEND = [
    (["li_bai", "su_shi"], "李白 × 苏轼 · 月下对饮"),
    (["li_bai", "du_fu"], "李白 × 杜甫 · 诗坛双圣"),
    (["su_shi", "xin_qiji"], "苏轼 × 辛弃疾 · 豪放词宗"),
    (["zhuge_liang", "zhang_heng"], "诸葛亮 × 张衡 · 奇技安邦"),
    (["li_yu", "nalan_xingde"], "李煜 × 纳兰 · 词帝词人"),
]

AI_DEFAULT = {
    "base_url": "https://api.deepseek.com",
    "model": "deepseek-chat",
    "temperature_chat": 0.9,
    "temperature_route": 0.7,
    "max_tokens_route": 3000,
    "max_tokens_chat": 800,
    "timeout": 60,
    "retries": 2,
}

# 解锁打卡所需最少对话轮数（用户发言次数）
UNLOCK_MIN_TURNS = 2

GLOBAL_CSS = """
<style>
/* —— 千年晤旅 · 古风主题 —— */
:root {
  --paper: #f7f1e3;      /* 宣纸米 */
  --paper-deep: #efe6d0;
  --ink: #3a3226;        /* 墨褐 */
  --ink-light: #8a7c66;
  --seal: #c0392b;       /* 印章红 */
  --gold: #b08d4f;       /* 描金 */
}
.stApp {
  background: linear-gradient(180deg, #faf5ea 0%, var(--paper) 40%, var(--paper-deep) 100%);
}
h1, h2, h3, h4 {
  font-family: "KaiTi", "STKaiti", "SimSun", serif !important;
  color: var(--ink) !important;
}
h1 { letter-spacing: 0.12em; }
p, li, label, span, div {
  font-family: "KaiTi", "STKaiti", "SimSun", "Microsoft YaHei", serif !important;
  color: var(--ink);
}
.block-container { padding-top: 2.2rem; max-width: 1150px; }
[data-testid="stSidebar"] {
  background: linear-gradient(180deg, #3d3323 0%, #2c2519 100%);
}
[data-testid="stSidebar"] * {
  font-family: "KaiTi", "STKaiti", "SimSun", "Microsoft YaHei", serif !important;
  color: #f2e8d5 !important;
}
[data-testid="stSidebar"] .stButton > button {
  background: transparent;
  border: 1px solid #8a7c66;
  color: #f2e8d5;
}
[data-testid="stSidebar"] .stButton > button:hover {
  border-color: var(--gold);
  color: #e8c87a;
}
.stButton > button, .stDownloadButton > button {
  background: linear-gradient(180deg, #8c2f24, #a63d2f);
  color: #fdf6e3 !important;
  border: 1px solid #6e241b;
  border-radius: 4px;
  letter-spacing: 0.15em;
}
.stButton > button:hover { background: linear-gradient(180deg, #a63d2f, #c0392b); }
.stButton > button[kind="secondary"] {
  background: transparent;
  color: var(--ink) !important;
  border: 1px solid var(--ink-light);
}
.stButton > button[kind="secondary"]:hover { border-color: var(--seal); color: var(--seal) !important; }
.stTextInput input, .stTextArea textarea, .stSelectbox [data-baseweb="select"] > div,
.stMultiSelect [data-baseweb="select"] > div, .stNumberInput input {
  background: #fffdf5 !important;
  border: 1px solid #cbbf9f;
  border-radius: 4px;
}
.stChatInput textarea { background: #fffdf5 !important; }
[data-testid="stExpander"] {
  background: rgba(255, 253, 245, 0.7);
  border: 1px solid #d8cbab;
  border-radius: 6px;
}
[data-testid="stMetric"] {
  background: rgba(255, 253, 245, 0.8);
  border: 1px solid #d8cbab;
  border-radius: 6px;
  padding: 0.6rem 1rem;
}
hr { border-color: #d8cbab; }
/* 印章样式 */
.qn-seal {
  display: inline-block;
  background: var(--seal);
  color: #fdf6e3;
  padding: 0.5rem 1.1rem;
  border-radius: 6px;
  letter-spacing: 0.25em;
  box-shadow: inset 0 0 0 2px rgba(255, 255, 255, 0.35);
  font-size: 1.05rem;
}
.qn-quote {
  border-left: 3px solid var(--gold);
  padding: 0.4rem 1rem;
  color: var(--ink-light);
  font-style: italic;
  letter-spacing: 0.08em;
}
.qn-card-title { letter-spacing: 0.2em; color: var(--seal) !important; }
/* —— 移动端适配（≤768px）—— */
@media (max-width: 768px) {
  .block-container { padding-top: 1rem; padding-left: .8rem; padding-right: .8rem; }
  /* 所有多列布局纵向堆叠：根治窄屏挤压与换行错乱 */
  [data-testid="stHorizontalBlock"] { flex-direction: column; }
  [data-testid="stHorizontalBlock"] > div { width: 100% !important; min-width: 0; }
  img, svg { max-width: 100%; height: auto; }
  h1 { letter-spacing: .06em; }
  h2, h3 { letter-spacing: .03em; }
  .qn-seal { font-size: .9rem; padding: .35rem .8rem; }
  .stButton > button { letter-spacing: .06em; }
}
</style>
"""
