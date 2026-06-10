#!/usr/bin/env python3
"""
A股短线量化追踪日报 — PDF 生成器 v2（全新排版）
简洁 · 专业 · 易读
"""
import json, os
from fpdf import FPDF

# ── 配色方案 ───────────────────────────────────────
NAVY    = (25, 45, 80)       # 深蓝 — 主标题/页眉
TEAL    = (0, 115, 135)      # 青蓝 — 强调色
WHITE   = (255, 255, 255)
BG_LIGHT = (247, 248, 250)   # 页背景
BG_CARD  = (240, 243, 248)   # 卡片背景
GRAY_D   = (55, 55, 55)      # 正文
GRAY_M   = (120, 120, 120)   # 辅助文字
GRAY_L   = (190, 190, 190)   # 边框
GRAY_XL  = (220, 220, 225)   # 极浅线
ROW_ALT  = (243, 245, 248)   # 表格交替行

FONT_PATH = r"C:\Windows\Fonts\simhei.ttf"


class ReportPDF(FPDF):

    def __init__(self):
        super().__init__("P", "mm", "A4")
        self.add_font("zh", "", FONT_PATH)
        self.add_font("zh", "B", FONT_PATH)
        self.set_auto_page_break(auto=True, margin=22)
        # 自定义边距
        self.l_margin = 20
        self.r_margin = 20
        self.content_w = 210 - self.l_margin - self.r_margin  # 170mm

    # ── 页眉 ───────────────────────────────────────
    def header(self):
        if self.page_no() == 1:
            return
        self.set_y(8)
        # 顶部分隔线
        self.set_draw_color(*TEAL)
        self.set_line_width(0.5)
        self.line(self.l_margin, 12, 210 - self.r_margin, 12)
        # 标题
        self.set_font("zh", "B", 7)
        self.set_text_color(*GRAY_M)
        self.cell(self.content_w, 5, "A股短线量化追踪日报  v2.1  |  2026-06-09",
                  align="R")
        self.ln(9)

    # ── 页脚 ───────────────────────────────────────
    def footer(self):
        self.set_y(-14)
        self.set_font("zh", "", 7)
        self.set_text_color(*GRAY_L)
        self.cell(self.content_w, 8, f"{self.page_no()}",
                  align="C")

    # ── 辅助元素 ───────────────────────────────────
    def _accent_line(self, y=None):
        """画一条强调线"""
        self.set_draw_color(*TEAL)
        self.set_line_width(0.6)
        if y:
            self.line(self.l_margin, y, 210 - self.r_margin, y)
        else:
            y = self.get_y()
            self.line(self.l_margin, y, 210 - self.r_margin, y)
            self.ln(4)

    def _section_gap(self, h=4):
        self.ln(h)

    # ── 章节标题 ──────────────────────────────────
    def section_h1(self, title):
        """一级标题 — 左侧色块 + 标题文字"""
        self.ln(2)
        x0 = self.get_x()
        y0 = self.get_y()
        # 色块
        self.set_fill_color(*TEAL)
        self.rect(x0, y0, 3, 7, style="F")
        # 标题
        self.set_xy(x0 + 6, y0)
        self.set_font("zh", "B", 12)
        self.set_text_color(*NAVY)
        self.cell(self.content_w - 6, 7, title)
        self.ln(10)

    def section_h2(self, title):
        """二级标题"""
        self.ln(1)
        self.set_font("zh", "B", 9)
        self.set_text_color(*GRAY_M)
        self.cell(0, 6, "  " + title)
        self.ln(7)

    # ── 正文段落 ──────────────────────────────────
    def body(self, text, size=9, color=None, indent=0):
        if color is None:
            color = GRAY_D
        self.set_font("zh", "", size)
        self.set_text_color(*color)
        prefix = " " * indent
        self.multi_cell(self.content_w - indent * 2, 5.5,
                        prefix + text)
        self.ln(1)

    def kv(self, key, val, size=9, k_color=None, v_color=None):
        """键值对单行"""
        if k_color is None:
            k_color = GRAY_D
        if v_color is None:
            v_color = GRAY_M
        self.set_font("zh", "B", size)
        self.set_text_color(*k_color)
        kw = self.get_string_width(key) + 4
        self.cell(kw, 6.5, key)
        self.set_font("zh", "", size)
        self.set_text_color(*v_color)
        self.cell(self.content_w - kw, 6.5, val)
        self.ln(6.5)

    # ── 卡片组件 ──────────────────────────────────
    def metric_card(self, title, value, subtitle, x, y, w, h=26):
        """单个指标卡片"""
        self.set_xy(x, y)
        self.set_fill_color(*BG_CARD)
        self.set_draw_color(*GRAY_XL)
        self.rect(x, y, w, h, style="DF")
        # 顶部强调条
        self.set_fill_color(*TEAL)
        self.rect(x, y, w, 2.5, style="F")
        # 标题
        self.set_xy(x + 3, y + 4.5)
        self.set_font("zh", "B", 7)
        self.set_text_color(*GRAY_M)
        self.cell(w - 6, 4, title, align="C")
        # 数值
        self.set_xy(x + 3, y + 10)
        self.set_font("zh", "B", 10)
        self.set_text_color(*NAVY)
        self.cell(w - 6, 6, value, align="C")
        # 副标题
        self.set_xy(x + 3, y + 18)
        self.set_font("zh", "", 6.5)
        self.set_text_color(*GRAY_M)
        self.cell(w - 6, 5, subtitle, align="C")

    def card_group(self, cards):
        """一排卡片：cards = [(title, value, sub), ...]"""
        n = len(cards)
        gap = 5
        cw = (self.content_w - gap * (n - 1)) / n
        y = self.get_y()
        for i, (title, value, sub) in enumerate(cards):
            x = self.l_margin + i * (cw + gap)
            self.metric_card(title, value, sub, x, y, cw)
        self.set_y(y + 30)

    # ── 表格组件 ──────────────────────────────────
    def styled_table(self, headers, rows, col_widths=None, font_size=7.5):
        """美观表格：深色表头 + 交替行 + 圆角感"""
        if not rows:
            return
        cw = col_widths or [self.content_w // len(headers)] * len(headers)

        # 表头
        self.set_font("zh", "B", font_size)
        self.set_fill_color(*NAVY)
        self.set_text_color(*WHITE)
        x0 = self.l_margin
        y0 = self.get_y()
        for i, h in enumerate(headers):
            self.set_xy(x0 + sum(cw[:i]), y0)
            self.cell(cw[i], 6.5, " " + h,
                      fill=True, align="C" if i > 0 else "L")
        self.ln(6.5)

        # 数据行
        self.set_font("zh", "", font_size)
        for idx, row in enumerate(rows):
            y = self.get_y()
            if y > 270:
                self.add_page()
                y = self.get_y()
            fill = idx % 2 == 0
            if fill:
                self.set_fill_color(*ROW_ALT)
            else:
                self.set_fill_color(*WHITE)
            for i, cell in enumerate(row):
                self.set_xy(x0 + sum(cw[:i]), y)
                self.set_text_color(*GRAY_D)
                align = "C" if i == 0 else "L"
                self.cell(cw[i], 6, " " + str(cell),
                          fill=True, align=align)
            self.ln(6)
        self.ln(4)

    # ── 列表项 ──────────────────────────────────
    def bullet(self, text, size=8.5, color=None):
        if color is None:
            color = GRAY_D
        self.set_font("zh", "", size)
        self.set_text_color(*color)
        self.cell(5, 6, "  -")
        self.cell(self.content_w - 5, 6, text)
        self.ln(6)


# ═════════════════════════════════════════════════
# 主生成函数
# ═════════════════════════════════════════════════

def build_pdf(data, output_path):
    pdf = ReportPDF()

    r = data.get("ranking", [])
    ldi_list = data.get("ldi_ranking", [])
    inds = data.get("indicators", {})
    dmi = inds.get("dmi", {})
    rpi = inds.get("rpi", {})
    rci = inds.get("rci", {})
    hm = data.get("hot_money", {})
    rfs_list = data.get("rfs_ranking", [])
    tq = data.get("three_questions", {})
    wl = data.get("watchlist", [])
    ea = data.get("earnings_alerts", {})
    signals = data.get("signals", [])
    checklist = data.get("checklist", [])

    regime = rci.get("regime", "轮动")
    advice = rci.get("advice", "")

    # ═══════════════ P1: 封面 ═══════════════

    pdf.add_page()
    pdf.ln(50)

    # 标题
    pdf.set_font("zh", "B", 28)
    pdf.set_text_color(*NAVY)
    pdf.cell(pdf.content_w, 14, "A股短线量化追踪日报", align="C")
    pdf.ln(18)

    # 副标题
    pdf.set_font("zh", "", 12)
    pdf.set_text_color(*GRAY_M)
    pdf.cell(pdf.content_w, 8, "Hot Money Quant Dashboard  v2.1", align="C")
    pdf.ln(16)

    # 日期
    pdf.set_font("zh", "B", 16)
    pdf.set_text_color(*TEAL)
    pdf.cell(pdf.content_w, 10, "2026-06-09  星期二", align="C")
    pdf.ln(20)

    # ---------- 三核模型摘要 — 三列布局 ----------
    regime_icon = {"强趋势": "█", "轮动": "█", "分歧": "█", "弱轮动": "█"}
    ri = regime_icon.get(regime, "█")
    summary_cards = [
        ("DMI  资金动量", f'{dmi.get("dmi_value", 0)/10000:.0f}亿', dmi.get("level", "")),
        ("RPI  抛压承接", f'{rpi.get("rpi_value", 0)/10000:.0f}亿', rpi.get("level", "")),
        ("RCI  市场格局", regime, advice[:12] + "…"),
    ]
    pdf.card_group(summary_cards)

    # 核心指标行
    pdf._accent_line()
    pdf.ln(2)
    metrics = [
        f"上证 {4010} +1.28%",
        f"深成指 {15268} +3.02%",
        f"创业板 {3961} +3.93%",
        f"科创50 {1663} +4.17%",
    ]
    pdf.set_font("zh", "", 8)
    pdf.set_text_color(*GRAY_M)
    sep = "   |   "
    line = sep.join(metrics)
    pdf.cell(pdf.content_w, 7, line, align="C")
    pdf.ln(12)

    # 底部 — 北向 + 涨停
    pdf.set_font("zh", "", 8.5)
    pdf.set_text_color(*GRAY_D)
    pdf.cell(pdf.content_w, 6,
             "北向资金: 净流入46.28亿（连续12日净买入）  |  涨停: 129家  连板: 10只  封板率: 84%",
             align="C")
    pdf.ln(30)

    # 底部免责
    pdf.set_font("zh", "", 6.5)
    pdf.set_text_color(*GRAY_L)
    pdf.multi_cell(pdf.content_w, 4,
                   "免责声明: 本报告基于 DMI/RPI/RCI/LDI/RFS 量化模型自动生成，"
                   "数据来源于东方财富/证券时报/财联社等公开渠道。"
                   "内容仅供参考，不构成投资建议。")

    # ═══════════════ P2: 行业排行榜 ═══════════════

    pdf.add_page()

    pdf.section_h1("行业资金流向排行榜")

    # 三张核心指标卡
    top_ind = r[0] if r else {}
    ldi_top = ldi_list[0] if ldi_list else {}
    rfs_top = rfs_list[0] if rfs_list else {}
    heat_cards = [
        ("主力净流入冠军", f'{top_ind.get("net_inflow",0)/10000:.0f}亿',
         top_ind.get("name", "-") + f' 涨{top_ind.get("price_pct",0):+.1f}%'),
        ("LDI 介入最深", f'LDI={ldi_top.get("ldi",0):.0f}',
         ldi_top.get("name", "-") + f' 成交占比{ldi_top.get("inflow_ratio",0):.0f}%'),
        ("RFS 回流确认", rfs_top.get("name", "-"),
         rfs_top.get("note", "-")[:18]),
    ]
    pdf.card_group(heat_cards)

    # 行业排行榜表格
    pdf.section_h2("Top 10 行业")
    headers = ["#", "行业", "主力净流入(万)", "5日净流入(万)", "涨跌幅", "热钱信号"]
    cw = [7, 44, 38, 38, 22, 26]
    rows = []
    for ind in r[:10]:
        sig = "[+]" if ind["net_inflow"] > 0 else "[-]"
        f5 = f'{ind["inflow_5d"]:+.0f}' if ind.get("inflow_5d") else "0"
        rows.append([str(ind["rank"]), ind["name"],
                     f'{ind["net_inflow"]:+.0f}', f5,
                     f'{ind["price_pct"]:+.2f}%', sig])
    pdf.styled_table(headers, rows, cw)

    # 热点信号摘要
    pdf.section_h2("热点信号")
    for sig in signals:
        icons = {"strong_inflow": "[集中]", "probing": "[试探]",
                 "strong_outflow": "[流出]", "overall_inflow": "[全市场]",
                 "inflow_today": "[流入]"}
        icon = icons.get(sig.get("type", ""), "[-]")
        pdf.kv(f"  {icon}  {sig.get('industry', '')}",
               f"  {sig.get('note', '')}", size=8)

    # 领涨个股
    pdf.section_h2("重点个股")
    stocks_text = (
        "电子: 生益科技+10.00%  东山精密+5.35%  风华高科+9.99%\n"
        "通信: 新易盛+8.38%  亨通光电+10.00%  长飞光纤+10.00%\n"
        "建材: 中国巨石+10.00%   |   机械: 英维克+10.00%\n"
        "特大单TOP: 新易盛+22亿  亨通光电+17亿  生益科技+14亿"
    )
    pdf.body(stocks_text, size=8)

    # ═══════════════ P3: LDI + RFS + 复盘 ═══════════════

    pdf.add_page()

    pdf.section_h1("资金介入深度  LDI")

    pdf.body("LDI（Liquidity Depth Index）综合净流入金额、成交占比、超大单比例、"
             "5日持续性四个维度，越高说明热钱介入越深。",
             size=7.5, color=GRAY_M)
    pdf.ln(2)

    headers = ["#", "题材", "LDI", "深度", "净流入(万)", "成交占比"]
    cw = [7, 50, 16, 22, 38, 30]
    depth_map = {"很深": "★★", "较深": "★", "一般": "△", "浅": "○"}
    rows = []
    for l in ldi_list[:8]:
        rows.append([
            str(l["rank"]), l["name"],
            f'{l["ldi"]:.1f}',
            depth_map.get(l.get("depth", ""), l.get("depth", "")),
            f'{l["net_inflow"]:+.0f}',
            f'{l.get("inflow_ratio", 0):.1f}%',
        ])
    pdf.styled_table(headers, rows, cw)

    # 热钱集中度
    pdf._section_gap()
    conc = hm.get("concentration", "")
    pdf.section_h2("热钱集中度")
    top3 = hm.get("top3_share", 0)
    pdf.kv("  Top3 占比", f"{top3:.1f}%", k_color=TEAL)
    conc_label = {"高度集中": "[高] 高度集中 — 资金高度集中于科技主线",
                  "中度集中": "[中] 中度集中 — 资金相对分散",
                  "分散": "[低] 分散 — 无明显资金合力"}
    pdf.kv("  判断", conc_label.get(conc, conc), size=8)

    # RFS
    pdf.section_h1("分歧回流强度  RFS")
    pdf.body("RFS（Reflow Strength）判断分歧后资金是否回补。"
             "回流确认 = 5日持续+今日双流入；试探 = 今日才回流。",
             size=7.5, color=GRAY_M)
    pdf.ln(1)
    for rf in rfs_list[:6]:
        icons = {"strong_reflow": "[回流确认]",
                 "reflow_trial": "[试探回流]",
                 "weak_outflow": "[持续流出]"}
        icon = icons.get(rf.get("signal", ""), "")
        pdf.kv(f"  {icon}  {rf['name']:12s}",
               f"RFS={rf['rfs']:.0f}  {rf.get('note', '')}",
               size=8)
    pdf.ln(3)

    # 三件事复盘
    pdf.section_h1("复盘三件事")
    for k in ["q1", "q2", "q3"]:
        q = tq.get(k, {})
        pdf.set_font("zh", "B", 9)
        pdf.set_text_color(*NAVY)
        pdf.cell(pdf.content_w, 6.5,
                 "  " + q.get("question", ""))
        pdf.ln(6.5)
        pdf.set_font("zh", "", 8.5)
        pdf.set_text_color(*GRAY_D)
        pdf.cell(pdf.content_w, 6.5,
                 "    " + q.get("answer", ""))
        pdf.ln(8)

    # ═══════════════ P4: 检查清单 + 关注股 + 明日观察 ═══════════════

    pdf.add_page()

    pdf.section_h1("每日检查清单")

    for item in checklist:
        status = "  [V]" if item.get("pass") else "  [X]"
        status_color = TEAL if item.get("pass") else (200, 60, 60)
        pdf.kv(f"  {status}  {item.get('item', '')}",
               item.get("detail", ""), size=8.5,
               k_color=status_color, v_color=GRAY_D)

    # 关注股
    pdf.section_h1("推荐关注股 & 财报预警")

    headers = ["股票", "代码", "推荐理由", "下次财报", "行业资金"]
    cw = [22, 18, 46, 28, 40]
    rows = []
    for w in wl:
        fs = w.get("flow_signal", "").replace("🟢", "[+]") \
            .replace("🔴", "[-]").replace("🟡", "[~]").replace("⚪", "[?]")
        rows.append([
            w.get("name", ""),
            w.get("code", ""),
            w.get("reason", "")[:14] + ("…" if len(w.get("reason", "")) > 14 else ""),
            w.get("expected_report_date", "待确认"),
            fs,
        ])
    pdf.styled_table(headers, rows, cw)
    pdf.set_font("zh", "", 8)
    pdf.set_text_color(*GRAY_M)
    pdf.cell(pdf.content_w, 6,
             f"财报状态: {ea.get('summary', '无数据')}")
    pdf.ln(8)

    # 明日观察
    pdf.section_h1("明日观察")
    top1_name = r[0]["name"] if r else ""
    tips = [
        f"{top1_name} 若续强则主线确立，回落则等待分歧低吸",
        "通信(光模块) 是当前最持续方向，关注分歧低吸机会",
        "北向资金连续12日净买入，外资态度积极",
        "连板高度仅3板（前日6板股跌停），晋级率14%，高位股风险",
        "热钱高度集中（Top3占74.8%），警惕科技股一致后的分化",
    ]
    for t in tips:
        pdf.bullet(t)

    # 免责
    pdf.ln(15)
    pdf._accent_line()
    pdf.set_font("zh", "", 6.5)
    pdf.set_text_color(*GRAY_L)
    pdf.multi_cell(pdf.content_w, 4,
                   "免责声明: 本报告基于 DMI/RPI/RCI/LDI/RFS 量化模型自动生成，"
                   "数据来源于东方财富/证券时报/财联社等公开渠道。"
                   "报告内容仅供参考，不构成任何投资建议。投资者据此操作，风险自担。")

    # ═══════════════ 输出 ═══════════════

    pdf.output(output_path)
    return output_path


if __name__ == "__main__":
    data_path = os.path.join(os.path.dirname(__file__), "_pdf_result.json")
    if not os.path.exists(data_path):
        print(f"错误: 找不到 {data_path}，请先运行分析")
        print("  python _trade_agent.py --stdin < data.json > _pdf_result.json")
        exit(1)
    data = json.load(open(data_path, "r", encoding="utf-8"))
    out = os.path.expanduser(r"~/Desktop/热钱量化追踪日报_2026-06-09.pdf")
    build_pdf(data, out)
    print(f"PDF 已保存: {out}  ({os.path.getsize(out):,} bytes)")
