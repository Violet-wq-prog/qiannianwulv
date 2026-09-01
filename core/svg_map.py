# -*- coding: utf-8 -*-
"""古风画卷风格路线地图（内联 SVG）。

交互地图与 GPS 定位留待未来迭代；本模块保证 Demo 阶段：
宣纸底、墨线串联站点、印章红点亮、全程已游加盖题跋印章。
中文由浏览器渲染，无字体问题。
"""
import html
import zlib

W, H = 920, 400


def _y_for(place_id: str) -> int:
    """稳定伪随机纵坐标（crc32 保证 rerun 之间一致）。"""
    return 120 + zlib.crc32(place_id.encode("utf-8")) % 130


def render_route_svg(route: dict, unlocked: list[bool]) -> str:
    sites = route["sites"]
    n = len(sites)
    all_done = bool(n) and all(unlocked)
    nodes = []
    for i, s in enumerate(sites):
        x = W / 2 if n == 1 else 80 + i * (W - 160) / (n - 1)
        nodes.append((x, _y_for(s["place_id"])))

    parts = []
    parts.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
        f'viewBox="0 0 {W} {H}" font-family="KaiTi,STKaiti,SimSun,serif">'
    )
    parts.append(f'<rect width="{W}" height="{H}" fill="#f7f1e3"/>')
    parts.append(f'<rect x="6" y="6" width="{W-12}" height="{H-12}" fill="none" '
                 f'stroke="#b08d4f" stroke-width="2"/>')
    parts.append(f'<rect x="12" y="12" width="{W-24}" height="{H-24}" fill="none" '
                 f'stroke="#3a3226" stroke-width="1" stroke-dasharray="6 4"/>')

    # 标题与图例
    parts.append(f'<text x="40" y="52" font-size="24" fill="#3a3226" '
                 f'letter-spacing="4">{html.escape(route["route_name"])}</text>')
    legend_y = 48
    parts.append(f'<circle cx="{W-190}" cy="{legend_y}" r="7" fill="#c0392b"/>'
                 f'<text x="{W-174}" y="{legend_y+7}" font-size="15" fill="#3a3226">已游</text>')
    parts.append(f'<circle cx="{W-110}" cy="{legend_y}" r="7" fill="none" stroke="#8a7c66" stroke-width="2"/>'
                 f'<text x="{W-94}" y="{legend_y+7}" font-size="15" fill="#3a3226">未游</text>')

    # 墨线串联
    if n > 1:
        pts = " ".join(f"{x:.0f},{y:.0f}" for x, y in nodes)
        parts.append(f'<polyline points="{pts}" fill="none" stroke="#4a3b2a" '
                     f'stroke-width="2.5" stroke-linejoin="round" opacity="0.75"/>')
    # 底色虚线山脉装饰
    parts.append(f'<path d="M 40,{H-60} Q 200,{H-150} 400,{H-70} T 880,{H-90}" '
                 f'fill="none" stroke="#c9bb9c" stroke-width="1.5" opacity="0.6"/>')

    # 站点节点
    for i, ((x, y), s) in enumerate(zip(nodes, sites)):
        done = bool(unlocked[i]) if i < len(unlocked) else False
        esc = html.escape(s["place_name"])
        if done:
            parts.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="15" fill="#c0392b"/>')
            parts.append(f'<rect x="{x-17:.0f}" y="{y-38:.0f}" width="34" height="20" fill="#c0392b" rx="3"/>')
            parts.append(f'<text x="{x:.0f}" y="{y-24:.0f}" font-size="13" fill="#fdf6e3" '
                         f'text-anchor="middle">已游</text>')
        else:
            parts.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="15" fill="#f7f1e3" '
                         f'stroke="#8a7c66" stroke-width="2.5"/>')
            parts.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="5" fill="#8a7c66"/>')
        parts.append(f'<text x="{x:.0f}" y="{y-52:.0f}" font-size="12" fill="#8a7c66" '
                     f'text-anchor="middle">第{s["day"]}天·第{s["seq"]}站</text>')
        parts.append(f'<text x="{x:.0f}" y="{y+40:.0f}" font-size="16" fill="#3a3226" '
                     f'text-anchor="middle" letter-spacing="1">{esc}</text>')

    # 全程已游：右侧竖排题跋印章
    if all_done:
        parts.append(
            f'<g transform="translate({W-56},150)">'
            f'<rect x="0" y="0" width="44" height="150" rx="6" fill="#c0392b" opacity="0.95"/>'
            f'<text x="22" y="34" font-size="18" fill="#fdf6e3" text-anchor="middle">全</text>'
            f'<text x="22" y="64" font-size="18" fill="#fdf6e3" text-anchor="middle">程</text>'
            f'<text x="22" y="94" font-size="18" fill="#fdf6e3" text-anchor="middle">已</text>'
            f'<text x="22" y="124" font-size="18" fill="#fdf6e3" text-anchor="middle">游</text>'
            f'</g>'
        )
    parts.append("</svg>")
    return "".join(parts)


def wrap_svg(svg: str) -> str:
    """画卷 HTML 包装：CSS 让 SVG 按容器宽等比缩放（SVG 自带 viewBox），
    移动端不再横向溢出。"""
    return (
        '<div class="qn-svg-wrap">'
        "<style>.qn-svg-wrap svg{width:100%;height:auto;display:block}</style>"
        f"{svg}</div>"
    )


def svg_wrap_html(route: dict, unlocked: list[bool]) -> str:
    """生成路线画卷 SVG 并套响应式包装（展示用；下载请用 render_route_svg）。"""
    return wrap_svg(render_route_svg(route, unlocked))
