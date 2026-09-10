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

# 单一视觉源：青绿山水主题，页面仅使用语义类名。
GLOBAL_CSS = """
<style>
:root { --paper:#f8f6ee; --paper-deep:#eaf0e9; --ink:#294b43; --ink-light:#65796f; --seal:#326b5c; --gold:#8fa795; --line:#d4ded3; }
.stApp { background:linear-gradient(145deg,#faf8f0,#eff3ec); color:var(--ink); }
.stApp p,.stApp li,.stApp label,.stApp input,.stApp textarea { font-family:"PingFang SC","Microsoft YaHei",sans-serif; line-height:1.8; }
h1,h2,h3,h4,.qn-home-title { font-family:"STKaiti","KaiTi","Songti SC",serif !important; color:var(--ink); font-weight:500; }
h1 { letter-spacing:.08em; }
.block-container { max-width:1280px; padding:2.5rem 2.5rem 4rem; }
[data-testid="stCaptionContainer"] p { color:var(--ink-light); }
[data-testid="stSidebar"] { background:#eaf0e8; border-right:1px solid var(--line); }
[data-testid="stSidebar"] .stButton button { width:100%; justify-content:flex-start; padding:.65rem 1rem; }
[data-testid="stSidebar"] .stButton button p { white-space:nowrap; }
[data-testid="stSidebar"] .stButton button[kind="secondary"] { background:transparent; border-color:transparent; }
[data-testid="stSidebar"] .stButton button[kind="secondary"]:hover { background:#dce8db; }
[data-testid="stSidebar"] [class*="st-key-nav_active_"] button[kind="secondary"] { background:#dce8db; border-left:3px solid #326b5c; }
.qn-steps li { margin:0; padding:0; }
.qn-home-hero picture { position:absolute; inset:0; }
[class*="st-key-person_card_"] .stButton button { width:100%; }
[data-testid="stSidebar"] [data-testid="stCaptionContainer"] { margin-top:.2rem; }
.stButton button,.stDownloadButton button { min-height:44px; border-radius:9px; border:1px solid #adc5b6; background:#fffdf6; color:var(--ink); transition:background .35s ease,border-color .35s ease; }
.stButton button:hover,.stDownloadButton button:hover { background:#e5eee3; border-color:#658e7b; color:var(--ink); }
.stButton button[kind="primary"] { background:var(--seal); color:#fffdf6; border-color:var(--seal); }
.stButton button[kind="primary"]:hover { background:#285a4d; }
.stButton button:disabled { opacity:.55; }
button:focus-visible { outline:3px solid #92b6a0 !important; outline-offset:3px; }
.stTextInput input,.stTextArea textarea,.stNumberInput input,[data-baseweb="select"] > div { background:#fffef8; border-radius:8px; color:var(--ink); }
[data-testid="stExpander"],[data-testid="stVerticalBlockBorderWrapper"],[data-testid="stVerticalBlock"][data-border="true"] { background:rgba(255,254,248,.75); border-color:var(--line); border-radius:12px; }
[data-testid="stMetric"] { background:#edf2e9; border-radius:10px; padding:.8rem 1rem; }
[data-testid="stChatMessage"] { background:#fffaf0; border:1px solid #e1e3d6; border-radius:16px; margin:.65rem 0; padding:1.2rem; }
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) { background:#e4eee5; border-color:#c5d7c9; }
[data-testid="stChatInput"] { border-color:#adc5b6; background:#fffef7; }
[data-baseweb="tab-highlight"] { background:var(--seal); }
hr { border-color:var(--line); }
.qn-quote { border-left:2px solid #8aac97; padding:.45rem 1rem; color:var(--ink-light); line-height:1.9; }
.qn-seal { display:inline-block; padding:.3rem .8rem; border:1px solid #6e9c83; border-radius:5px; color:#326b5c; background:#e3eee1; letter-spacing:.15em; }
.qn-card-title { color:var(--seal); }
.qn-steps { display:grid; grid-template-columns:repeat(8,minmax(0,1fr)); gap:.5rem; padding:1rem; margin:0 0 1.75rem; list-style:none; background:#f1f5ee; border:1px solid var(--line); border-radius:12px; }
.qn-steps li { text-align:center; font-size:.78rem; color:#748479; }
.qn-steps span { display:block; margin:0 auto .35rem; width:1.65rem; height:1.65rem; line-height:1.65rem; border-radius:50%; background:#dfe7dc; }
.qn-steps li.current { color:#235848; font-weight:600; }
.qn-steps li.current span { background:#326b5c; color:white; }
.qn-steps li.past span { background:#d0e1d2; color:#326b5c; }
[class*="st-key-person_card_"] { background:linear-gradient(160deg,#fdfcf5,#edf3e9); border:1px solid var(--line); border-radius:14px; padding:1.2rem; }
[class*="st-key-person_card_"] [data-testid="stImage"] { display:flex; justify-content:center; }
[class*="st-key-person_card_"] img { object-fit:contain; max-height:180px; }
.qn-person-name { font-family:"Songti SC",serif; font-size:1.65rem; letter-spacing:.12em; margin:.2rem 0; }
.qn-context { border-left:3px solid #7b9f8b; border-radius:0 12px 12px 0; background:linear-gradient(90deg,#e5eee3,#f8f7ef); padding:1rem 1.35rem; margin:.4rem 0 1.25rem; }
.qn-context strong { display:block; font-family:"Songti SC",serif; font-size:1.45rem; color:#2b5a4d; }
.qn-context small { color:#637a6b; }
[class*="st-key-timeline_"] { position:relative; margin-left:.7rem; padding:1rem 1.2rem 1.2rem 1.7rem; border-left:2px solid #c9daca; border-radius:0 12px 12px 0; background:#fffdf6; }
[class*="st-key-timeline_"]::before { content:""; position:absolute; width:12px; height:12px; border-radius:50%; left:-7px; top:1.55rem; background:#e0e8db; border:2px solid #b8cfbd; }
[class*="st-key-timeline_done_"]::before { background:#477e66; border-color:#dce9d9; }
[class*="st-key-journal_entry_"] { padding:1.7rem; background:repeating-linear-gradient(#fffdf6 0,#fffdf6 31px,#eef0e6 32px); border:1px solid var(--line); border-radius:8px; }
.qn-chapter { color:#597b67; font-size:.8rem; letter-spacing:.18em; border-bottom:1px solid var(--line); padding:.6rem 0; margin:1.5rem 0 .8rem; }
.qn-home-hero { position:relative; overflow:hidden; isolation:isolate; min-height:540px; border:1px solid var(--line); border-radius:16px; background:#f6f1e6; display:flex; align-items:center; padding:clamp(1.5rem,4vw,4rem); }
.qn-home-hero-image { position:absolute; inset:0; z-index:0; width:100% !important; height:100% !important; max-width:none !important; object-fit:cover; object-position:center; animation:qnArrive 2s ease both,qnBreathe 16s ease-in-out 2s infinite alternate; }
.qn-home-hero::after { content:""; position:absolute; inset:0; z-index:1; pointer-events:none; background:radial-gradient(ellipse at 70% 50%,#f8f5e966,transparent 40%); animation:qnMist 18s ease-in-out infinite alternate; }
.qn-home-copy { position:relative; z-index:2; width:43%; animation:qnArrive 1.8s ease both; }
.qn-home-eyebrow { font-size:.8rem; letter-spacing:.2em; color:#5b766b; }
.qn-home-title { font-size:clamp(2.5rem,4.5vw,4.6rem) !important; line-height:1.3; white-space:nowrap; margin:1rem 0; }
.qn-home-subtitle { font-size:1.15rem; line-height:1.8; margin:1rem 0; }
.qn-home-description { font-size:.95rem; line-height:1.9; color:#5d7366; }
.st-key-home_hero_action { margin:.6rem 0 1.7rem; }
@keyframes qnArrive { from { opacity:0; transform:translateY(8px); } to { opacity:1; transform:translateY(0); } }
@keyframes qnBreathe { from { transform:scale(1); } to { transform:scale(1.015); } }
@keyframes qnMist { from { opacity:.2; transform:translateX(-1%); } to { opacity:.4; transform:translateX(1%); } }
@media(max-width:1050px) {
 .qn-home-hero { padding:2rem; }
 .qn-home-copy { width:65%; background:rgba(248,245,235,.88); padding:1rem; border-radius:10px; }
}
@media(max-width:768px) {
 .block-container { padding:1.2rem .9rem 3rem; }
 [data-testid="stHorizontalBlock"] { flex-direction:column; }
 [data-testid="stHorizontalBlock"] > div { width:100% !important; min-width:0; }
 img,svg { max-width:100%; }
 .qn-steps { grid-template-columns:repeat(4,minmax(0,1fr)); gap:.7rem .3rem; padding:.75rem; }
 .qn-home-hero { padding:17rem 1.2rem 1.5rem; min-height:0; }
 .qn-home-hero-image { height:340px !important; object-position:right top; mask-image:linear-gradient(#000 65%,transparent); }
 .qn-home-copy { width:100%; padding:0; background:transparent; }
 .qn-home-title { font-size:2.65rem !important; }
 .qn-context { padding:.9rem; }
 [class*="st-key-person_card_"] { height:auto; }
 [class*="st-key-timeline_"] { margin-left:.4rem; padding:1rem 1rem 1rem 1.2rem; }
}
@media(prefers-reduced-motion:reduce) { .qn-home-hero-image,.qn-home-copy,.qn-home-hero::after { animation:none !important; } .stButton button,.stDownloadButton button { transition:none; } }
</style>
"""
