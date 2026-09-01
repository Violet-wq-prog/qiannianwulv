# 🏮 千年晤旅 · 沉浸式历史人文游历交互平台

面向文旅与传统文化科普的沉浸式 AI 交互平台。以**历史人物第一人称**讲述真实往事与内心想法，
把"打卡式旅游"变成一场与古人同游的成套人文旅程。

## 两条使用入口

### 🗺️ 入口A · 文旅旅游完整链路（一体化串联）

```
地点检索（支持 GPS 定位找附近故地）→ 选定同行历史人物 → 填写游玩偏好
→ AI 融合【你的喜好 + 古人真实生平爱好经历】生成成套路线（模式A人物视角优先 / 模式B双向融合）
→ 画卷地图 / 实景交互地图（点击站点直达）→ 逐站点【故地重游对话】（支持语音朗读回复）
→ 完成对话解锁打卡 → 上传自拍生成"我与古人同游"合影 → 写游历随笔
→ 地图点位点亮 → 整套旅程存入个人游历档案
→ 导出路线长图 / 行程单 / 分享卡片（含二维码）
```

### 💬 入口B · 日常对话

搜索/推荐历史人物 → 单人第一人称畅谈（回复可语音朗读）；拉多位不同朝代人物开**跨时代群聊**
（李白×苏轼月下对饮、李白×杜甫诗坛双圣、苏轼×辛弃疾豪放词宗、诸葛亮×张衡奇技安邦……）
群聊各成员回复并发请求，5 人一轮约 10-20 秒。

### 🎯 年轻化玩法

**古今人格测试**（六题测出你的古代人格）· **古人赠藏头诗**（名字嵌入诗中、落款古人）·
**时空票根**（旅程结束后生成古风纪念票根收藏）· **同游合影**（AI 合成）· **分享卡片**（真二维码）

## 快速开始

```bash
cd qiannian
pip install -r requirements.txt          # streamlit / openai / python-dotenv / Pillow / pydeck / edge-tts
streamlit run app.py                      # 打开 http://localhost:8501
```

### AI 配置

`.env` 中配置（已默认复用本机旧项目的 DeepSeek key）：

```
AI_API_KEY=sk-xxxx
AI_BASE_URL=https://api.deepseek.com
AI_MODEL=deepseek-chat
```

任何 OpenAI 兼容服务均可（改 `AI_BASE_URL` / `AI_MODEL` 即可）。

### 离线演示模式（无 key / 断网也全程可演示）

```bash
AI_DISABLED=1 streamlit run app.py       # Windows cmd: set AI_DISABLED=1 && streamlit run app.py
```

路线由人物库内置足迹文本程序化拼装、对话降级到关键词应答、群聊降级到预置剧本、
实景地图自动切换无底图模式、语音朗读给出友好提示——
**地点检索 → 路线 → 对话 → 打卡 → 合影 → 随笔 → 档案 → 导出全链路闭环不受影响**。

## 全链路冒烟测试

```bash
python scripts/smoke_test.py          # 约 37 项：全链路 + 新人物数据 + 离线剧本 + 缓存 + 导出 + 地图 + GPS 兜底
python scripts/check_portraits.py     # 立绘就绪校验（透明通道 / 尺寸 / 数量）
```

## 内容与资源

- **人物库** `data/people.py`：17 位史料可考人物（苏轼、李白、李清照、毕昇、诸葛亮、张衡、
  沈括、王维、白居易、辛弃疾、杜甫、屈原、陆游、张九龄、李煜、仓央嘉措、纳兰性德），
  每人含性格/口吻/事迹/爱好/名句/第一人称自述 + 各地点【事迹-故事-开场白】预写文本
  （既是 AI 素材，也是离线降级内容源）。
- **地点库** `data/places.py`：37 处故地（含真实经纬度），支持古称别名检索（钱塘→杭州、长安→西安、
  金陵→南京、黄州→黄冈）。
- **人物立绘** `assets/characters/`：17 位 Q版国风 IP 立绘已就位（512×768 透明底），
  如需调整可按 `assets/characters/portrait_prompts.md` 的提示词重新生成，
  用 `python scripts/import_portraits.py "文件夹"` 导入，跑 `python scripts/check_portraits.py` 校验。
- **地图**：双地图并存——①古风画卷 SVG（宣纸底、墨线串联、印章红点亮，响应式缩放，可下载 .svg）；
  ②实景交互地图（pydeck，点击站点圆点直达该站对话，离线自动切无底图）。
- **GPS**：寻访故地页可浏览器定位（需 localhost/https），显示最近故地公里数；拒绝/失败自动回退手动选城。
- **语音**：聊天页可朗读最新回复（edge-tts，男古人默认云希、李清照用晓晓）；语音输入已接入
  浏览器 Web Speech API（Chrome/Edge 免 key；识别文本自动发送；失败回退文字输入），
  未来可无缝替换为离线 ASR 模型（core/asr.py 已留 transcribe() 接口）。
- **导出分享**：路线长图（PNG）、行程单（Markdown）、分享卡片（票根 + 真二维码），全部下载字节缓存。
- **数据**：SQLite（`data/qiannian.db`，首次运行自动创建），旅程/打卡/随笔/照片/对话全部落盘，档案页随时回看；
  档案页底部可**删除整段旅程**（两步确认，打卡/随笔/照片记录与合影文件一并清理）。

## 性能与体验优化（本次迭代）

- **AI 流式对话**：单人闲谈 / 故地重游回复逐字浮现（st.write_stream），离线与失败自动降级离线文本，聊天不中断。
  群聊并发生成、**完成一条浮现一条**（打字机效果），不再干等最慢成员。
- **语音输入**：浏览器原生 Web Speech API（Chrome/Edge，免安装免 key）——点按钮说话，
  识别文本自动作为消息发出；不支持/断网时友好提示并回退文字输入，离线演示不受影响。
- AI 确定性调用缓存（路线生成/群聊开场/藏头诗/随笔润色同参数零重复付费）；群聊成员并发回复；
  重试退避、失败不缓存（断网不冻结）。
- 字体/立绘/背景/蒙版进程级缓存，合影与票根合成提速；SVG/导出字节 st.cache_data 缓存；
  数据库短连接显式提交+关闭；图片 `width="stretch"` 自适应。
- 移动端适配：全局 `@media` 断点（多列自动竖排、图片/SVG 等比缩放）、古风主题 `.streamlit/config.toml`、
  聊天页自动滚动到底部、pills 窄屏自动换行。
- 冒烟测试强化：页面渲染异常（含被 app.py 兜底转成 st.error 的）一律拦截报错，37 项全链路回归。

## 项目结构

```
app.py                  唯一入口：session_state 状态机路由（视图惰性导入）
config.py               页面枚举 / 偏好选项 / AI 参数 / 古风全局样式（含移动端断点）
core/                   state 状态机 · data_loader 双向索引 · database SQLite
                        ai_client AI封装(降级开关+流式) · prompt_templates 提示词
                        route_builder 路线校验+降级 · scripts 离线剧本
                        photo_utils 合影合成 · svg_map 画卷地图 · interactive_map 实景地图
                        geo GPS定位 · tts 语音朗读 · asr 语音输入(Web Speech) · export 导出分享
views/                  13 个页面视图（home/explore/person_profile/preference/route_gen/
                        route_view/site_dialogue/photomontage/journal/archive/chat_solo/chat_group/
                        ancient_test 古今人格测试）
data/                   people.py 人物库(17) · places.py 地点库(37) · qiannian.db
assets/                 characters 立绘(含 portrait_prompts.md 提示词) · backgrounds 背景 · photos 合影
scripts/                smoke_test.py 冒烟测试 · check_portraits.py 立绘校验
                        generate_placeholders.py 占位图生成
                        make_poster/make_ppt/make_pdfs/make_zip 提交材料生成 · record_demo 演示录屏
submission/             iCAN 提交材料：海报/PPT/演示视频/开发日志/设计说明书/产品介绍文案/
                        系统摘要/演示视频解说字幕文案/源码包
```

## iCAN 提交材料（submission/）

生成顺序：`python scripts/record_demo.py`（真实录屏 + 截图）→
`python scripts/make_poster.py` · `make_ppt.py` · `make_pdfs.py` · `make_zip.py`。
材料已按大赛官方规则制作：内容为最新版、动态地图/动态数字人仅列未来迭代、PPT 无无关佐证、
演示为真实原生录屏；AI 辅助说明以专项声明呈现（PPT 末页 AI辅助说明 / 开发日志文末 AI辅助声明 /
海报角落小字 / 视频片尾字幕），不在正文逐段标注。

## 未来迭代方向（对应设计文档）

动态数字人 · 离线 ASR 模型接入（在线语音输入已可用）· 移动端网页/PWA · 全国地点库持续扩充 · 用户社交分享

## 开发说明

本项目由 AI 辅助开发（原型实现、内容整理与测试验证）。
