#!/usr/bin/env python3
"""
A股短线量化追踪系统 v2.1 — 报告生成器

将 _trade_agent.py 输出的 JSON 渲染为格式化文本报告。
使用方式:
  python _trade_agent.py --stdin < data.json | python _trade_report.py
  python _trade_agent.py --auto | python _trade_report.py
"""

import json
import sys
from datetime import date

# ── 终端颜色（兼容 Windows） ─────────────────────────

def _c(code: str, text: str) -> str:
    """包裹 ANSI 转义码"""
    return f"\033[{code}m{text}\033[0m"

def red(s):    return _c("31", s)
def green(s):  return _c("32", s)
def yellow(s): return _c("33", s)
def blue(s):   return _c("34", s)
def magenta(s): return _c("35", s)
def cyan(s):   return _c("36", s)
def gray(s):   return _c("90", s)
def bold(s):   return _c("1", s)
def dim(s):    return _c("2", s)

CHECK = "✓"
CROSS = "✗"
WARN  = "!"


# ── 表格渲染 ──────────────────────────────────────────

def _table(headers: list, rows: list, widths: list = None) -> str:
    """生成简单的对齐表格"""
    if not rows:
        return "  (无数据)"

    # 自动列宽
    if not widths:
        widths = [len(h) for h in headers]
        for row in rows:
            for i, cell in enumerate(row):
                cell_str = str(cell) if cell is not None else ""
                # 中文算2个宽度
                width = sum(2 if ord(c) > 127 else 1 for c in cell_str)
                if i < len(widths):
                    widths[i] = max(widths[i], width)

    # 表头
    sep = "─" * (sum(widths) + len(widths) * 3 + 1)
    lines = [f"  ┌{sep}┐"]

    header_line = "  │"
    for i, h in enumerate(headers):
        w = widths[i]
        hw = sum(2 if ord(c) > 127 else 1 for c in h)
        padding = w - hw
        header_line += f" {bold(h)}{' ' * padding} │"
    lines.append(header_line)
    lines.append(f"  ├{sep}┤")

    # 数据行
    for row in rows:
        line = "  │"
        for i, cell in enumerate(row):
            cell_str = str(cell) if cell is not None else ""
            w = widths[i]
            cw = sum(2 if ord(c) > 127 else 1 for c in cell_str)
            padding = w - cw
            line += f" {cell_str}{' ' * padding} │"
        lines.append(line)

    lines.append(f"  └{sep}┘")
    return "\n".join(lines)


# ── 信号图标映射 ─────────────────────────────────────

SIGNAL_ICONS = {
    "strong_inflow":   "🟢",
    "mild_inflow":     "🟢",
    "inflow_today":    "🟢",
    "probing":         "🟡",
    "strong_outflow":  "🔴",
    "outflow_warn":    "🟠",
    "overall_inflow":  "📊",
    "overall_outflow": "📊",
}


# ── 报告渲染主函数 ───────────────────────────────────

def render_report(data: dict, use_color: bool = True) -> str:
    """渲染完整分析报告"""
    global red, green, yellow, blue, magenta, cyan, gray, bold, dim
    if not use_color:
        def noop(s, text=""):
            if callable(s):
                return text
            return s
        red = green = yellow = blue = magenta = cyan = gray = dim = lambda t: t
        bold = lambda t: t.upper()

    today = data.get("date", date.today().isoformat())
    summary = data.get("summary", {})
    indicators = data.get("indicators", {})
    dmi = indicators.get("dmi", {})
    rpi = indicators.get("rpi", {})
    rci = indicators.get("rci", {})
    ranking = data.get("ranking", [])
    checklist = data.get("checklist", [])
    signals = data.get("signals", [])
    regime = rci.get("regime", "未知")
    advice = rci.get("advice", "")
    regime_color = rci.get("color", "gray")

    lines = []

    # ── 标题 ──
    lines.append("")
    lines.append(bold(f"  ═══════════════════════════════════════════"))
    lines.append(bold(f"    A股短线量化追踪日报 {data.get('version', 'v2.1')}"))
    lines.append(bold(f"    {today}"))
    lines.append(bold(f"  ═══════════════════════════════════════════"))
    lines.append("")

    # ── 市场格局 ──
    color_map = {"green": green, "yellow": yellow, "red": red, "gray": gray}
    rc = color_map.get(regime_color, yellow)
    lines.append(bold("  【市场格局】") + rc(bold(f" {regime}")))
    lines.append(f"  ├─ DMI: {dmi.get('dmi_value', 0):.0f} ({dmi.get('level', '')}) ─ {dmi.get('label', '')}")
    lines.append(f"  ├─ RPI: {rpi.get('rpi_value', 0):.0f} ({rpi.get('level', '')}) ─ {rpi.get('label', '')}")
    lines.append(f"  └─ RCI: {regime} ─ {rc(advice)}")
    lines.append("")

    # ── 龙头数据 ──
    main_line = summary.get("main_line", "")
    limit_up_total = summary.get("limit_up_total", 0)
    lianban_total = summary.get("lianban_total", 0)
    lines.append(bold(f"  龙头板块: {main_line}"))
    lines.append(f"  涨停 {limit_up_total}家 | 连板 {lianban_total}只")
    lines.append("")

    # ── 行业排行榜 ──
    lines.append(bold("  【行业排行榜 TOP10】"))
    headers = ["排名", "行业", "DMI", "RPI", "净流入(万)", "5日净流入", "信号"]
    rows = []
    for ind in ranking[:10]:
        strength = ind.get("strength", "")
        icon_map = {
            "strong_inflow": green("→↑"),
            "mild_inflow": green("→"),
            "inflow_today": green("→"),
            "weak_inflow": yellow("→"),
            "weak_outflow": yellow("↓"),
            "strong_outflow": red("↓↓"),
        }
        icon = icon_map.get(strength, "  ")
        rows.append([
            str(ind["rank"]),
            ind["name"],
            f"{ind['dmi']:.0f}",
            f"{ind['rpi']:.0f}",
            f"{ind['net_inflow']:+.0f}" if ind['net_inflow'] else "0",
            f"{ind['inflow_5d']:+.0f}" if ind['inflow_5d'] else "0",
            icon,
        ])
    lines.append(_table(headers, rows))
    lines.append("")

    # ── 热点信号 ──
    lines.append(bold("  【热点信号】"))
    for sig in signals:
        icon = SIGNAL_ICONS.get(sig.get("type", ""), "•")
        industry = sig.get("industry", "")
        note = sig.get("note", "")
        lines.append(f"  {icon} {bold(industry)} ─ {note}")
    lines.append("")

    # ── 每日检查清单 ──
    lines.append(bold("  【每日检查清单】"))
    for idx, item in enumerate(checklist):
        status = green(CHECK) if item.get("pass") else red(CROSS)
        detail = item.get("detail", "")
        name = item.get("item", "")
        lines.append(f"  {status} {bold(f'{idx+1}.')} {name}: {detail}")
    lines.append("")

    # ── 执行方向 ──
    lines.append(bold("  【执行方向】"))
    regime_actions = {
        "强趋势": f"    {green('→ 核心主线明确，聚焦')} {bold(main_line)} {green('板块龙头')}",
        "轮动": f"    {yellow('→ 板块轮动，只在分歧日低吸')} {bold(main_line)} {yellow('等方向，不追涨')}",
        "分歧": f"    {red('→ 市场分歧大，减少操作，观望为主')}",
        "弱轮动": f"    {gray('→ 多看少动，等待明确信号')}",
    }
    lines.append(regime_actions.get(regime, f"    {advice}"))
    lines.append("")

    # ── 明日观察重点 ──
    # ── 截图新增: LDI 资金介入深度排名 ──
    ldi_ranking = data.get("ldi_ranking", [])
    if ldi_ranking:
        lines.append(bold("  【LDI 资金介入深度排名】") + dim(" — 越高说明热钱介入越深"))
        headers_ldi = ["排名", "题材", "LDI", "深度", "净流入(万)", "成交占比"]
        rows_ldi = []
        for l in ldi_ranking[:8]:
            depth_icon = {"很深": green("◆◆"), "较深": green("◆"), "一般": yellow("◇"), "浅": gray("○")}
            di = depth_icon.get(l.get("depth", ""), "  ")
            rows_ldi.append([
                str(l["rank"]), l["name"],
                f"{l['ldi']:.1f}", f"{di} {l['depth']}",
                f"{l['net_inflow']:+.0f}" if l['net_inflow'] else "0",
                f"{l.get('inflow_ratio', 0):.1f}%"
            ])
        lines.append(_table(headers_ldi, rows_ldi))
        lines.append("")

    # ── 截图新增: 热钱集中度 ──
    hot_money = data.get("hot_money", {})
    if hot_money and hot_money.get("shares"):
        conc = hot_money.get("concentration", "")
        conc_icon = {"高度集中": "🔥", "中度集中": "💧", "分散": "🌊"}
        ci = conc_icon.get(conc, "")
        lines.append(bold(f"  【热钱集中度】{ci} {conc}"))
        lines.append(f"  Top3 占比 {hot_money.get('top3_share', 0):.1f}% | 总流入 {hot_money.get('total_inflow', 0):.0f}万")
        top3_names = [s["name"] for s in hot_money.get("shares", [])[:3]]
        lines.append(f"  主要集中在: {' / '.join(top3_names)}")
        lines.append("")

    # ── 截图新增: RFS 回流强度 ──
    rfs_list = data.get("rfs_ranking", [])
    if rfs_list:
        lines.append(bold("  【RFS 分歧回流强度排名】") + dim(" — 回流越强说明分歧后有资金回补"))
        rfs_icons = {
            "strong_reflow": green("回流确认"),
            "reflow_trial": yellow("试探回流"),
            "weak_outflow": gray("持续流出"),
            "outflow_warning": red("转向流出"),
        }
        for r in rfs_list[:5]:
            ri = rfs_icons.get(r.get("signal", ""), "  ")
            lines.append(f"  {ri} {bold(r['name'])} — {r['note']} (RFS={r['rfs']:.0f})")
        lines.append("")

    # ── 截图新增: 三件事复盘框架 ──
    three_q = data.get("three_questions", {})
    if three_q:
        lines.append(bold("  【三件事复盘框架】") + dim(" — 截图复盘用法"))
        for k in ["q1", "q2", "q3"]:
            q = three_q.get(k, {})
            if q:
                lines.append(f"  {bold(q.get('question', ''))}")
                lines.append(f"    → {q.get('answer', '')}")
        lines.append("")

    # ── 截图新增: 题材对比 ──
    compare = data.get("compare", {})
    if compare and "error" not in compare:
        a = compare.get("sector_a", {})
        b = compare.get("sector_b", {})
        verdict = compare.get("verdict", "")
        if a and b:
            lines.append(bold(f"  【题材对比】{a.get('name', '')} vs {b.get('name', '')}"))
            lines.append(f"    {a.get('name', '')}: 净流入{a.get('net_inflow', 0):+.0f}万 涨{a.get('pct', 0):+.1f}% LDI={a.get('ldi', 'N/A')}")
            lines.append(f"    {b.get('name', '')}: 净流入{b.get('net_inflow', 0):+.0f}万 涨{b.get('pct', 0):+.1f}% LDI={b.get('ldi', 'N/A')}")
            lines.append(f"    {bold('结论')}: {verdict}")
            lines.append("")

    # ── 新增: 推荐关注股 & 财报预警 ──
    watchlist = data.get("watchlist", [])
    earnings = data.get("earnings_alerts", {})
    if watchlist:
        lines.append(bold("  【📋 推荐关注股 & 财报预警】"))
        # 表格
        headers_w = ["股票", "代码", "推荐理由", "下次财报", "行业信号"]
        rows_w = []
        for w in watchlist:
            rows_w.append([
                w.get("name", ""),
                w.get("code", ""),
                w.get("reason", "")[:10] + ("..." if len(w.get("reason", "")) > 10 else ""),
                w.get("expected_report_date", "待确认"),
                w.get("flow_signal", "⚪"),
            ])
        lines.append(_table(headers_w, rows_w))

        # 财报预警
        alerts_list = earnings.get("alerts", [])
        if alerts_list:
            lines.append(f"  {bold('财报预警')}: {earnings.get('summary', '')}")
            for a in alerts_list[:5]:
                if a.get("level") in ("🔴", "🟡"):
                    lines.append(f"  {a['level']} {a['message']}")
        lines.append("")

    # ── 明日观察重点 ──
    lines.append(bold("  【明日观察】"))
    top1_name = ranking[0]["name"] if ranking else ""
    top2_name = ranking[1]["name"] if len(ranking) > 1 else ""
    if regime == "强趋势":
        lines.append(f"  • {top1_name} 若继续Top3流入，确认主线，可积极参与")
        lines.append(f"  • {top2_name} 若放量突破，可适当关注")
    elif regime == "轮动":
        lines.append(f"  • {top1_name} 若明日继续Top3流入，确认主线强度")
        lines.append(f"  • 若 {top1_name} 回落，等待分歧日低吸机会")
        lines.append(f"  • 关注是否有新板块（{top2_name} 等）接力")
    else:
        lines.append(f"  • 等待 {top1_name} 确认持续性，不急于入场")
        lines.append(f"  • 观察是否有板块逆势走强")

    # 北向资金
    north_net = None
    try:
        north_net = next(
            (item["detail"] for item in checklist if "北向" in item["item"]),
            None
        )
    except Exception:
        pass
    if north_net:
        lines.append(f"  • {north_net}")
    lines.append("")

    return "\n".join(lines)


# ── CLI ───────────────────────────────────────────────

def main():
    try:
        raw = sys.stdin.read()
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"错误: JSON 解析失败 — {e}", file=sys.stderr)
        print(f"用法: python _trade_agent.py --stdin | python _trade_report.py", file=sys.stderr)
        sys.exit(1)

    # 判断是否支持颜色
    use_color = sys.stdout.isatty()

    report = render_report(data, use_color=use_color)
    print(report)


if __name__ == "__main__":
    main()
