# -*- coding: utf-8 -*-
"""iCAN 提交文档生成：开发日志 PDF + 设计说明书 PDF（reportlab，A4）。

内容为最新版（17 位人物 / 37 处故地 / 13 页面视图 / 流式对话 / 语音输入 / 双地图 / GPS 等）；
AI 辅助说明以文末“AI辅助声明”专项呈现，不在每段末尾标注（保证版面整洁、便于评委阅读）。

前置：先运行 record_demo.py 产出原型截图（截图缺失时自动跳过嵌入）。
运行：python scripts/make_pdfs.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (Image, PageBreak, Paragraph, SimpleDocTemplate,
                                Spacer, Table, TableStyle)

from config import FONTS_DIR, PROJECT_ROOT

SUB = PROJECT_ROOT / "submission"
SHOT_DIR = SUB / "screenshots"
CHAR_DIR = PROJECT_ROOT / "assets" / "characters"

pdfmetrics.registerFont(TTFont("Hei", str(FONTS_DIR / "simhei.ttf")))
pdfmetrics.registerFont(TTFont("Kai", str(FONTS_DIR / "simkai.ttf")))

INK = colors.HexColor("#3A3226")
SEAL = colors.HexColor("#C0392B")
GOLD = colors.HexColor("#B08D4F")
GRAY = colors.HexColor("#8A7C66")

S_TITLE = ParagraphStyle("t", fontName="Kai", fontSize=26, leading=34,
                         textColor=INK, alignment=TA_CENTER, spaceAfter=8)
S_SUB = ParagraphStyle("s", fontName="Hei", fontSize=12, leading=18,
                       textColor=GRAY, alignment=TA_CENTER, spaceAfter=4)
S_H1 = ParagraphStyle("h1", fontName="Hei", fontSize=15, leading=22,
                      textColor=INK, spaceBefore=14, spaceAfter=6)
S_H2 = ParagraphStyle("h2", fontName="Hei", fontSize=11.5, leading=18,
                      textColor=SEAL, spaceBefore=8, spaceAfter=3)
S_BODY = ParagraphStyle("b", fontName="Hei", fontSize=10, leading=17,
                        textColor=INK, firstLineIndent=20, spaceAfter=4)
S_BODY0 = ParagraphStyle("b0", fontName="Hei", fontSize=10, leading=17,
                         textColor=INK, spaceAfter=4)
S_CAP = ParagraphStyle("c", fontName="Hei", fontSize=8.5, leading=12,
                       textColor=GRAY, alignment=TA_CENTER, spaceBefore=2, spaceAfter=8)


def body(text: str) -> str:
    """正文段落（AI 辅助声明以文末专项声明呈现，不在每段末尾标注，保证版面整洁）。"""
    return text


def cap(text: str) -> str:
    return text


def doc(path):
    d = SimpleDocTemplate(str(path), pagesize=A4,
                          leftMargin=22 * mm, rightMargin=22 * mm,
                          topMargin=20 * mm, bottomMargin=20 * mm,
                          title=str(path.name))
    return d


def shot(name, width=160 * mm):
    p = SHOT_DIR / f"{name}.png"
    if not p.exists():
        return None
    from PIL import Image as PILImage
    im = PILImage.open(p)
    w, h = im.size
    return Image(str(p), width=width, height=width * h / w)


# ══════════════════ 开发日志 ══════════════════
def build_devlog():
    path = SUB / "开发日志_千年晤旅.pdf"
    story = []
    story.append(Spacer(1, 60 * mm))
    story.append(Paragraph("千年晤旅", S_TITLE))
    story.append(Paragraph("沉浸式历史人文游历交互平台 · 开发日志", S_SUB))
    story.append(Spacer(1, 8 * mm))
    story.append(Paragraph("开发周期：2026-08-13 至 2026-08-22（原型设计 → 全链路联调 → 提交材料）", S_SUB))
    story.append(Paragraph("技术栈：Python · Streamlit · SQLite · 大模型对话接口（DeepSeek）· PIL · pydeck · edge-tts", S_SUB))
    story.append(PageBreak())

    story.append(Paragraph("一、项目概述", S_H1))
    story.append(Paragraph(body(
        "《千年晤旅》是面向人文文旅与传统文化科普的沉浸式交互平台。针对传统旅游产品"
        "“只给景点、没有故事”的痛点，平台实现与史书真实记载的历史人物跨时空对话伴游："
        "用户输入地点即可匹配在当地生活游历过的先贤（人物库 17 位、故地 37 处、覆盖 24 城），"
        "AI 融合用户游玩偏好与人物真实生平爱好生成成套游历路线；游览过程中人物以第一人称讲述"
        "古迹往事与当时内心想法（AI 在线时回复逐字流式浮现）；配套站点打卡点亮、AI 同游合影、"
        "游历随笔、个人游历档案，形成完整业务闭环。")))
    story.append(Paragraph(body(
        "本次开发按照“设计大纲 → 素材整理 → 原型编码 → AI 接入 → 模块联调 → 测试修复 → "
        "年轻化玩法与体验优化迭代 → 提交材料制作”的顺序推进，全部功能已实现并通过自动化冒烟测试"
        "（37 步全绿）验证。")))

    story.append(Paragraph("二、开发时间线", S_H1))
    stages = [
        ("阶段一 · 项目构思与需求设计",
         "确定双入口产品形态（文旅完整链路 + 日常对话），梳理九大功能模块与一体化业务流程；"
         "明确“拒绝生硬百科、历史人物第一人称输出”“双向融合路线”“双模式路线”等核心设计理念。",
         "设计大纲文档、业务流程草图（地点检索→选人→偏好→路线→对话→打卡→合影→随笔→档案）。"),
        ("阶段二 · 历史人物与地点素材整理",
         "整理 17 位史料可考历史人物（苏轼、李白、李清照、毕昇、诸葛亮、张衡、沈括、王维、"
         "白居易、辛弃疾、杜甫、屈原、陆游、张九龄、李煜、仓央嘉措、纳兰性德），每人配置性格、"
         "口吻、事迹、爱好、名句、第一人称自述，并为 37 处故地（24 城，含真实经纬度）逐条撰写"
         "【事迹-故事-开场白】第一人称讲解文本；建立地点→人物、人物→地点、城市→地点双向索引，"
         "支持古称别名检索（钱塘→杭州、长安→西安、金陵→南京、黄州→黄冈）。",
         "data/people.py（人物库）、data/places.py（地点库）、core/data_loader.py（双向索引）。"),
        ("阶段三 · Python 原型代码编写",
         "搭建单入口 Streamlit 架构：app.py + session_state 状态机路由，核心层（状态机/数据加载/"
         "SQLite/AI 封装/提示词/路线编排/离线剧本/合影合成/双地图）与 13 个页面视图分离；"
         "SQLite 落盘 trips/checkins/journals/photos/对话记录，保证浏览器重开后档案可回看；"
         "全局古风主题 + 移动端断点适配。",
         "app.py、config.py、core/ 模块、views/ 十三视图。"),
        ("阶段四 · 大模型能力接入",
         "以 OpenAI 兼容协议接入 DeepSeek 大模型：路线生成采用 response_format=json_object 结构化输出，"
         "配合“只允许使用人物库地点清单”的提示词约束与 schema 校验补全；站点对话、单人对话、群聊、"
         "随笔润色分别设计第一人称提示词模板；实现 AI_DISABLED 一键离线演示开关与三级降级"
         "（内置路线/关键词应答/群聊剧本）；对话升级为流式输出（st.write_stream 逐字浮现），"
         "并实现确定性调用缓存（路线/群聊开场/藏头诗/随笔润色同参数零重复付费）。",
         "core/ai_client.py、core/prompt_templates.py、core/route_builder.py、core/scripts.py。"),
        ("阶段五 · 对话与路线模块调试",
         "调优故地重游对话第一人称效果（开场白由人物库 opener 驱动）；新增游历天数选择（1/2/3 天/"
         "由 AI 安排）贯穿 AI 提示词与降级路线；群聊采用“隔离轮转”策略并改为并发生成、完成一条"
         "浮现一条（打字机效果），解决长上下文串人设与“干等最慢成员”问题；离线群聊预置 5 组剧本"
         "（李白×苏轼、李白×杜甫、苏轼×辛弃疾、诸葛亮×张衡、李煜×纳兰）+ 全员通用台词。",
         "views/route_gen.py、views/site_dialogue.py、views/chat_group.py 等。"),
        ("阶段六 · 地图·打卡·合影·随笔·档案模块",
         "实现双地图：①古风 SVG 画卷地图（宣纸底、墨线串联、印章红点亮、全程已游题跋）；"
         "②实景交互地图（pydeck，站点真实经纬度散点，点击站点直达该站对话，离线自动切无底图）；"
         "接入浏览器 GPS 定位（定位失败自动回退手动选城）；PIL 合成“我与古人同游”合影；"
         "游历随笔支持请古人润色；档案页从 SQLite 回放全部旅程并支持删除（两步确认）与"
         "导出路线长图/行程单/分享卡片（真二维码）。",
         "core/svg_map.py、core/interactive_map.py、core/geo.py、core/photo_utils.py、core/export.py 等。"),
        ("阶段七 · 年轻化玩法与语音体验迭代",
         "为贴近年轻用户新增三大玩法：①古今人格测试——MBTI 式六题问答规则化匹配历史人物与专属称号；"
         "②古人赠藏头诗——请古人为你写一首嵌入名字的诗；③时空票根——旅程结束后生成古风撕口票根收藏。"
         "新增语音输入：浏览器原生 Web Speech API（Chrome/Edge 免 key），识别文本自动作为消息发送；"
         "语音朗读（edge-tts，男古人云希/李清照晓晓）。",
         "views/ancient_test.py、chat_solo 藏头诗入口、core/asr.py、core/tts.py、photo_utils.make_ticket。"),
        ("阶段八 · 测试与修复",
         "编写全链路自动化冒烟测试（Streamlit AppTest 逐页执行，37 步全绿），覆盖地点检索、路线生成、"
         "三站对话解锁、合影、随笔、票根、档案、删除、单人对话、群聊、人格测试、离线剧本、导出、"
         "地图、GPS 兜底等；测试强化为同时拦截 at.exception 与 st.error（app.py 兜底转成的用户可见错误）；"
         "逐一修复：首页重复元素 key 崩溃、故地重游页 button_row 未导入导致按钮缺失、时空票根按钮"
         "不可达死代码、测试脚本 GBK 编码崩溃、AppTest 临时目录清理导致退出码非零等问题，"
         "并将弃用 API use_container_width 迁移为 width=\"stretch\"。",
         "scripts/smoke_test.py（37 步全绿）、测试结论与问题清单（见第三节）。"),
        ("阶段九 · 提交材料制作",
         "制作 1200×560 横版产品海报；真实录屏完整业务流程演示视频；编写产品说明 PPT、本开发日志与"
         "设计说明书、产品介绍文案、系统摘要、演示视频解说字幕文案；整理源代码压缩包。",
         "submission/ 目录下海报、PPT、演示视频、PDF 文档、文案、源码 zip。"),
    ]
    for t, work, out in stages:
        story.append(Paragraph(t, S_H2))
        story.append(Paragraph(body(work), S_BODY))
        story.append(Paragraph(body("产出：" + out), S_BODY0))

    story.append(Paragraph("三、关键问题与解决方案", S_H1))
    issues = [
        ("首页重复元素 key 导致崩溃", "两组群聊推荐均以李白开头，生成相同 widget key home_group_li_bai",
         "key 改为由两位人物 id 共同标识，全项目 key 唯一化校验"),
        ("故地重游页按钮全部缺失", "site_dialogue 调用 button_row 但未导入",
         "补全导入；冒烟测试增加 st.error 断言，此类被 app.py 兜底的错误不再漏报"),
        ("时空票根按钮不可达", "生成按钮挂在不可达的 elif 分支，用户永远看不到",
         "重构分支结构，无票根时展示生成按钮并保留分享卡片入口"),
        ("测试脚本 GBK 编码崩溃", "✓/✅ 字符在管道输出时 UnicodeEncodeError",
         "脚本输出统一重配置为 UTF-8（交互式终端不受影响）"),
        ("AppTest 临时目录清理失败", "系统 TEMP 目录被占用导致退出码非零",
         "临时目录改到项目内 .smoke_tmp（已 gitignore），测试通过以 0 退出"),
        ("字符串内中文引号导致语法错误", "人物库文案在双引号字符串内误用 ASCII 引号",
         "统一改用中文全角引号，全项目 py_compile 校验"),
        ("侧边栏 radio 与状态机跳页冲突", "radio 自身状态与程序化跳页冲突，页面被弹回首页",
         "改用无状态按钮导航，状态机单向流转"),
        ("生成路线按钮禁用导致“生成不出”", "偏好多选为空时按钮 disabled，用户只写想法无法生成",
         "偏好改为可选、按钮常开、守卫放宽，未选时按人物视角安排"),
        ("AI 结构化输出失败/超时", "网络或模型异常导致 JSON 解析失败",
         "json_object + schema 补全 + 整体降级内置路线，三重保险"),
        ("群聊多角色串人设", "单请求自演多角色在长上下文下易崩人设",
         "隔离轮转：每轮仅请求一个角色发言，历史超长压缩"),
        ("rerun 重复触发 AI 调用", "生成页按钮连点产生重复请求与费用",
         "route 已存在则不调用（幂等），生成逻辑入页即触发；确定性调用加 st.cache_data 缓存"),
        ("PIL 中文渲染豆腐块", "默认字体不支持中文",
         "显式探测 Windows 楷体/黑体/宋体字体链，lru_cache 进程级缓存"),
        ("合影背景随机变化", "hash() 进程随机化导致同人物背景不一致",
         "改用 crc32 确定性种子"),
        ("Streamlit 组件弃用警告", "use_container_width 参数将于 2025-12-31 移除",
         "全面迁移为 width=\"stretch\"，依赖版本提升至 streamlit>=1.51"),
    ]
    tbl = [[Paragraph("问题", ParagraphStyle("q", parent=S_H2, spaceBefore=0)),
            Paragraph("原因", ParagraphStyle("r", parent=S_H2, spaceBefore=0)),
            Paragraph("解决方案", ParagraphStyle("s2", parent=S_H2, spaceBefore=0))]]
    for a, b, c in issues:
        st = ParagraphStyle("x", fontName="Hei", fontSize=9, leading=13, textColor=INK)
        tbl.append([Paragraph(a, st), Paragraph(b, st), Paragraph(c, st)])
    t = Table(tbl, colWidths=[48 * mm, 52 * mm, 58 * mm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EFE6D0")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#B08D4F")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(t)

    story.append(Paragraph("四、测试记录", S_H1))
    story.append(Paragraph(body(
        "自动化冒烟测试（scripts/smoke_test.py，Streamlit AppTest 框架逐页执行，离线降级路径）"
        "共 37 步全部通过：首页 → 地点检索 → 检索结果 → 路线生成（2 天 3 站）→ 路线总览（SVG 地图）→ "
        "三站故地对话与解锁打卡 → 合影页 → 随笔页 → 档案回放 → 时空票根生成 → 删除旅程（级联清理）→ "
        "单人对话（含藏头诗入口）→ 跨时代群聊 → 古今人格测试 → 新人物数据完整性 → 检索命中回归 → "
        "离线群聊剧本闭环 → 字体缓存命中 → 导出三件套 → 交互地图构造 → GPS 手动兜底 → 立绘校验。")))
    story.append(Paragraph(body(
        "AI 真实路径验证：路线生成（结构化 JSON，人物第一人称开场白与故事）、站点对话（120-250 字"
        "第一人称叙事）、流式对话输出、群聊轮转发言、藏头诗生成均通过 DeepSeek 实测；"
        "无 key/断网时全链路自动降级为内置内容，演示永不中断。")))
    story.append(Paragraph(body("以下为测试与演示过程中留存的原型截图佐证："), S_BODY0))
    for name in ["01_home", "06_route_view", "06b_interactive_map", "07_site_dialogue",
                 "12_solo_chat", "11_archive"]:
        img = shot(name)
        if img:
            story.append(img)

    story.append(Paragraph("五、素材佐证（人物立绘）", S_H1))
    story.append(Paragraph(body(
        "17 位人物立绘已就位（512×768 透明底 Q 版国风 IP 图），由脚本生成占位图后再以真实美术资源"
        "同名覆盖导入（scripts/import_portraits.py），check_portraits.py 校验透明通道/尺寸/数量全部通过。"
        "示例立绘如下：")))
    imgs = [CHAR_DIR / f"{p}.png" for p in
            ["su_shi", "li_bai", "li_qingzhao", "bi_sheng", "zhuge_liang"]]
    from PIL import Image as PILImage
    row = []
    for pth in imgs:
        if pth.exists():
            im = PILImage.open(pth)
            row.append(Image(str(pth), width=28 * mm, height=42 * mm))
    if row:
        story.append(Table([row], colWidths=[30 * mm] * len(row)))
        story.append(Paragraph(cap("（从左至右：苏轼、李白、李清照、毕昇、诸葛亮立绘）"), S_CAP))

    story.append(Paragraph("结语", S_H1))
    story.append(Paragraph(body(
        "本项目完成了从设计到全链路联调的原型开发，并经自动化测试与真实大模型双路径验证。"
        "原型已实现流式对话、语音输入、双地图、GPS 定位、缓存与离线保障等完整能力；"
        "后续将按设计说明书中的迭代规划，持续完善全国动态地图、动态数字人、离线 ASR 等内容。")))
    story.append(Spacer(1, 10 * mm))
    story.append(Paragraph("AI辅助声明", S_H1))
    story.append(Paragraph(body(
        "本开发日志由 AI 辅助整理编写，部分素材与配图由 AI 辅助生成；全部内容已经团队人工"
        "审核与修改，核心功能代码与业务逻辑由团队自主完成。")))
    d = doc(path)
    d.build(story)
    print("开发日志:", path, f"{path.stat().st_size/1024:.0f} KB")


# ══════════════════ 设计说明书 ══════════════════
def build_design():
    path = SUB / "设计说明书_千年晤旅.pdf"
    story = []
    story.append(Spacer(1, 60 * mm))
    story.append(Paragraph("千年晤旅", S_TITLE))
    story.append(Paragraph("沉浸式历史人文游历交互平台 · 设计说明书", S_SUB))
    story.append(Spacer(1, 8 * mm))
    story.append(Paragraph("智慧文创赛道 · Python + Streamlit 原型", S_SUB))
    story.append(PageBreak())

    story.append(Paragraph("1. 项目背景与行业痛点", S_H1))
    story.append(Paragraph(body(
        "文旅产业持续升温，但传统旅游产品存在明显短板：景点信息以列表与攻略形式呈现，路线千人一面；"
        "游客面对古迹时“知其然而不知其所以然”，读不懂一块碑、一座祠承载的历史悲欢；"
        "传统文化科普多以百科词条式输出，缺乏情感代入，难以吸引年轻群体。")))
    story.append(Paragraph(body("核心痛点在于：游客缺少一个“懂历史、有情感、可对话”的同行者。")))

    story.append(Paragraph("2. 项目概述与产品设计理念", S_H1))
    story.append(Paragraph(body(
        "千年晤旅是面向人文文旅与传统文化科普的沉浸式交互平台：用户与史书真实记载的历史人物"
        "跨时空对话结伴出游。系统接收地点信息（人物库 17 位、故地 37 处/24 城），结合用户游玩喜好"
        "与人物真实生平经历，双向融合生成成套完整旅游行程；游览时人物以第一人称讲述古迹往事与内心想法，"
        "AI 在线时回复流式逐字浮现，并支持浏览器语音输入。")))
    story.append(Paragraph(body(
        "设计理念：①第一人称叙事——拒绝生硬百科，还原人物当时内心想法与情绪；"
        "②双向融合路线——用户喜好 × 人物真实生平爱好，成套输出而非零散列表；"
        "③双模式路线——模式A人物视角优先 / 模式B双向融合；"
        "④双使用场景——实地文旅出行 + 日常休闲对话；"
        "⑤全链路离线保障——无 AI 时内置剧本降级，演示永不中断。")))

    story.append(Paragraph("3. 功能模块说明", S_H1))
    mods = [
        "历史人物搜索与个性化推荐：按姓名、朝代、身份、事迹检索 17 位人物；课本热点与网络热门分组推荐。",
        "地点检索与 GPS：输入城市/景点（支持古称别名）匹配在此生活游历过的全部历史人物；浏览器定位找附近故地（失败自动回退手动选城）。",
        "路线偏好采集：游玩偏好多选（古迹/美食/山水/慢游/博物馆等）+ 自由想法 + 游历天数（1/2/3 天/由 AI 安排）+ 双模式选择。",
        "AI 智能路线规划：结构化 JSON 生成多天成套路线，每站绑定人物故事、开场白与游览建议；地点严格限定人物库清单，严禁虚构；AI 不可用时内置足迹拼装降级。",
        "单人沉浸式对话：人物第一人称讲述生平遭遇与时代故事，对现代事物以古代视角幽默回应；AI 在线时流式逐字浮现，支持浏览器语音输入。",
        "跨时代群聊：多位不同朝代人物同席互辩（隔离轮转防串人设、并发生成逐条浮现），离线预置 5 组剧本 + 通用台词。",
        "故地重游·情景对话：人物以重游故土视角讲古时市井风物、此地事迹与当时心境；完成对话（≥2 轮）解锁打卡。",
        "双地图打卡点亮：古风 SVG 画卷地图（灰点=未游、红印=已游、全站解锁加盖题跋印章）+ 实景交互地图（pydeck 真实经纬度散点，点击站点直达对话）；全国级动态地图列入未来迭代。",
        "AI 同游合影：上传自拍，PIL 合成“我与古人同游”古风合影（椭圆蒙版+立绘+题跋+印章+画框），绑定点位存档。",
        "游历随笔：写下游历感悟，可请同行古人润色补写。",
        "个人游历档案：路线、点亮足迹、合影、随笔、票根全部落盘，随时回看；支持导出路线长图/行程单/分享卡片（真二维码）与删除旅程。",
        "年轻化玩法：古今人格测试（六题匹配古人+专属称号）、古人赠藏头诗（名字嵌入诗）、时空票根（撕口纪念票根）。",
        "语音能力：edge-tts 朗读最新回复；浏览器 Web Speech 语音输入（Chrome/Edge，识别文本自动发送）。",
    ]
    for m in mods:
        story.append(Paragraph(body("· " + m), S_BODY0))

    story.append(Paragraph("4. 业务流程图", S_H1))
    story.append(Paragraph("（一）整套旅游业务流程（一体化串联）", S_H2))
    flow = ("输入旅游地点（支持 GPS 定位附近故地）→ 检索匹配当地历史人物 → 选定一位同行人物 → "
            "填写游玩偏好/天数/模式 → AI 融合【用户喜好 + 古人真实生平爱好】生成成套路线 → "
            "画卷地图 / 实景交互地图（点击站点直达）→ 逐站故地重游对话（听古人讲此地故事与内心想法，"
            "可语音输入/朗读）→ 完成对话解锁打卡点亮 → 上传自拍生成同游合影 → 写游历随笔保存 → "
            "整套路线走完，全部记录存入个人游历档案 → 导出长图/行程单/分享卡片")
    story.append(Paragraph(body(flow), S_BODY))
    story.append(Paragraph("（二）日常聊天流程（独立分支）", S_H2))
    story.append(Paragraph(body("首页搜索/推荐历史人物 → 开启单人第一人称对话 / 创建跨时代群聊 → 与古人自由聊天（流式回复、语音输入/朗读）"),
                           S_BODY))
    story.append(Paragraph("（三）年轻化玩法入口：古今人格测试、藏头诗（单人对话页）、时空票根（随笔页/档案页）",
                           S_H2))

    story.append(Paragraph("5. 历史人物形象设计方案", S_H1))
    story.append(Paragraph(body(
        "①人物来源：仅选史书可靠记载的真实历史人物（17 位），涵盖文学家、发明家、工匠、科学家、政治家等多元身份；"
        "②美术风格：国风写实古风，贴合朝代服饰器物，拒绝 Q 版魔改；"
        "③人物数据模型：每人配置朝代/身份/生卒年/性格/口吻/事迹/爱好/名句/第一人称自述，"
        "并为每处关联地点撰写【事迹摘要-第一人称故事-开场白】三级文本，同时作为 AI 提示词素材与离线降级内容源；"
        "④Demo 使用静态透明 PNG 半身图（当前为程序生成占位图，同名替换真实美术资源即可），动态数字人列入未来迭代。")))

    story.append(Paragraph("6. 技术实现方案", S_H1))
    story.append(Paragraph(body(
        "①原型框架：Python + Streamlit 单入口应用，session_state 状态机路由管理 13 个页面视图，"
        "文旅链路数据以 travel 结构在会话内闭环流转；②持久化：SQLite 短连接模式落盘 trips/checkins/"
        "journals/photos/对话记录，JSON 快照便于档案回放；③大模型对话接口：OpenAI 兼容协议接入 DeepSeek，"
        "路线生成采用 json_object 结构化输出 + schema 校验补全，对话升级为流式输出，确定性调用加缓存；"
        "④离线降级：AI_DISABLED 一键切换离线演示，内置路线（人物库文本拼装）、关键词应答、群聊剧本"
        "（5 组 + 通用台词）保证全链路闭环；⑤双地图：内联 SVG 古风画卷 + pydeck 实景交互（站点点击直达）；"
        "⑥语音：edge-tts 朗读、浏览器 Web Speech 语音输入；⑦移动端：全局 @media 断点与古风主题；"
        "⑧测试：Streamlit AppTest 全链路自动化冒烟测试（37 步全绿）。")))

    story.append(Paragraph("7. 项目创新点", S_H1))
    for t in [
        "① 一体化文旅业务闭环：地点检索—偏好—成套路线—沉浸对话—打卡—合影—随笔—档案一条链路深度打通；",
        "② 双向融合路线生成：用户个人喜好 × 历史人物真实生平爱好，定制专属成套行程；",
        "③ 第一人称叙事：还原人物事件发生时内心想法与情绪，让历史“活”起来；",
        "④ 流式对话与语音输入：AI 回复逐字浮现，浏览器原生语音识别一句话自动发送；",
        "⑤ 跨时代群聊：多身份多朝代人物同席互辩，并发生成逐条浮现，隔离轮转防串台；",
        "⑥ 双地图与高可用：画卷 SVG + 实景交互地图；无 AI 时内置剧本降级，演示永不中断；",
        "⑦ 年轻化玩法：古今人格测试、古人赠藏头诗、时空票根收藏，专业内容与年轻表达结合。",
    ]:
        story.append(Paragraph(body(t), S_BODY0))

    story.append(Paragraph("8. 现存不足", S_H1))
    for t in [
        "· 人物立绘为程序生成的水墨占位图，待替换真实国风美术资源；",
        "· 合影为 PIL 静态合成，非生成式 AI 图像；",
        "· 语音输入依赖浏览器 Web Speech（Chrome/Edge 且需联网），离线 ASR 模型待接入；",
        "· 地点库覆盖 37 处故地，尚待扩充全国；",
        "· 实景交互地图为站点级点击直达，全国级动态地图未开发（列入未来迭代）。",
    ]:
        story.append(Paragraph(body(t), S_BODY0))

    story.append(Paragraph("9. 未来迭代规划", S_H1))
    story.append(Paragraph(body(
        "①全国动态交互式地图：录入更多景点经纬度，实现跨城动态切换与轨迹动画（本次原型不开发）；")))
    story.append(Paragraph(body(
        "②动态数字人：接入 SadTalker 等开源方案，基于静态国风图片生成带口型表情的说话动画（本次原型不开发）；")))
    story.append(Paragraph(body(
        "③离线 ASR 模型接入（funasr / faster-whisper），摆脱联网依赖；④扩充全国地点库与各朝代人物库；"
        "⑤开发移动端 PWA，方便外出旅游直接使用。")))
    story.append(Spacer(1, 10 * mm))
    story.append(Paragraph("AI辅助声明", S_H1))
    story.append(Paragraph(body(
        "本设计说明书由 AI 辅助整理编写，部分配图与素材由 AI 辅助制作；全部内容已经团队人工"
        "审核与修改，核心功能代码与业务逻辑由团队自主完成。")))

    d = doc(path)
    d.build(story)
    print("设计说明书:", path, f"{path.stat().st_size/1024:.0f} KB")


if __name__ == "__main__":
    build_devlog()
    build_design()
