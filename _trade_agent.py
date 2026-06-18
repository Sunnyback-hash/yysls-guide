#!/usr/bin/env python3
"""
A股短线量化追踪系统 v2.1 — 分析引擎

功能:
  1. 接收外部数据（通过 --data JSON 或 stdin）执行 DMI/RPI/RCI 分析
  2. 提供纯计算函数，供 Claude Agent 调用后格式化输出
  3. 包含数据获取函数（备用，尝试东财公开API，失败时返回空数据）

使用方式:
  # Agent 模式（推荐）：Claude 用 WebSearch 获取数据，传给此脚本分析
  echo '<json_data>' | python _trade_agent.py --stdin

  # 离线模式：传入 JSON 文件
  python _trade_agent.py --data '{"industries": [...], "market_index": [...]}'

  # 自动模式：尝试从东财 API 获取数据（不保证成功）
  python _trade_agent.py --auto

输出: 结构化 JSON 到 stdout
"""

import json
import sys
import os
import argparse
from datetime import date, datetime

VERSION = "v2.1"

# ── DMI 权重系数 ─────────────────────────────────────
WEIGHT_TOP1 = 1.5      # Top1 板块涨停额外权重
WEIGHT_LIANBAN = 1.2   # 连板权重
WEIGHT_ZHA_BAN = 1.3   # 炸板权重

# 市场格局阈值
DMI_HIGH = 2000
DMI_MEDIUM = 800
RPI_HIGH = 3000


# ═══════════════════════════════════════════════════════
# 核心计算函数（纯数学，无外部依赖）
# ═══════════════════════════════════════════════════════

def calc_dmi(industries: list, lianban_count: int = 0) -> dict:
    """
    DMI = Σ(板块涨停家数) + Top1涨停×权重 + Σ(连板涨停×权重)

    输入 industry 格式: [{"name":"电子","net_inflow":1234,"inflow_5d":567,...}, ...]
    净流入为正 = 资金买入，为负 = 资金卖出
    """
    total_inflow = sum(
        ind.get("net_inflow", 0) for ind in industries
        if ind.get("net_inflow", 0) > 0
    )
    total_outflow = abs(sum(
        ind.get("net_inflow", 0) for ind in industries
        if ind.get("net_inflow", 0) < 0
    ))

    top1 = industries[0] if industries else {}
    top1_inflow = top1.get("net_inflow", 0)
    top1_contribution = max(0, top1_inflow) * WEIGHT_TOP1
    lianban_contribution = lianban_count * 50 * WEIGHT_LIANBAN

    dmi_value = total_inflow + top1_contribution + lianban_contribution
    dmi_net = dmi_value - total_outflow

    # 使用数据自适应阈值
    _high = max(DMI_HIGH, total_inflow * 0.3)
    _med = max(DMI_MEDIUM, total_inflow * 0.1)

    if dmi_value >= _high:
        level, label = "高", "资金动量强，市场有明确主线"
    elif dmi_value >= _med:
        level, label = "中", "资金动量中等，板块轮动为主"
    else:
        level, label = "低", "资金动量弱，市场观望或分歧"

    return {
        "dmi_value": round(dmi_value, 2),
        "dmi_outflow": round(total_outflow, 2),
        "dmi_net": round(dmi_net, 2),
        "level": level,
        "label": label,
        "top1_contribution": round(top1_contribution, 2),
        "lianban_contribution": round(lianban_contribution, 2),
    }


def calc_rpi(industries: list, zhaban_count: int = 0, max_lianban: int = 0) -> dict:
    """
    RPI = |连板家数总和| + Σ(炸板家数×权重)

    用行业主力净流出总量 + 连板拥堵 + 炸板冲击 来估算抛压
    """
    total_outflow = abs(sum(
        ind.get("net_inflow", 0) for ind in industries
        if ind.get("net_inflow", 0) < 0
    ))
    congestion = max_lianban * 100 * WEIGHT_LIANBAN
    zhaban_impact = zhaban_count * 80 * WEIGHT_ZHA_BAN
    rpi_value = total_outflow + congestion + zhaban_impact

    _high = max(RPI_HIGH, total_outflow * 0.5)

    if rpi_value >= _high:
        level, label = "高", "抛压较大，追高风险高，适合低吸"
    elif rpi_value >= _high * 0.5:
        level, label = "中", "抛压中等，注意盘中分歧"
    else:
        level, label = "低", "抛压小，筹码相对稳定"

    return {
        "rpi_value": round(rpi_value, 2),
        "level": level,
        "label": label,
        "congestion": round(congestion, 2),
        "zhaban_impact": round(zhaban_impact, 2),
    }


def calc_rci(dmi: dict, rpi: dict, north_net: float = 0,
             limit_up_count: int = 0, dmi_net: float = 0) -> dict:
    """
    RCI = 买入总量 + 卖出总量 + 余量

    市场格局分类:
    - 强趋势: DMI高 + RPI可控 + 北向流入 + 净流入为正
    - 轮动:   DMI中等 + 涨停足够
    - 分歧:   DMI低 + 涨停少 + 净流出大
    """
    dmi_val = dmi.get("dmi_value", 0)
    rpi_val = rpi.get("rpi_value", 0)
    total_inflow = dmi_val + dmi.get("dmi_outflow", 0)

    # 数据自适应阈值
    dmi_high_adaptive = max(DMI_HIGH, total_inflow * 0.3)
    dmi_med_adaptive = max(DMI_MEDIUM, total_inflow * 0.1)
    rpi_high_adaptive = max(RPI_HIGH, rpi_val * 0.8)

    rci_score = dmi_val - rpi_val * 0.6 + north_net * 10 + limit_up_count * 30

    if dmi_val >= dmi_high_adaptive and rpi_val < rpi_high_adaptive and north_net > 0 and dmi_net > 0:
        regime, advice, color = "强趋势", "核心主线明确，可积极做多，追涨龙头或分歧低吸均可", "green"
    elif dmi_val >= dmi_med_adaptive and limit_up_count >= 30 and dmi_net > -500:
        regime, advice, color = "轮动", "板块轮动为主，只在分歧日低吸，不追涨", "yellow"
    elif dmi_val < dmi_med_adaptive or limit_up_count < 20 or dmi_net < -1000:
        regime, advice, color = "分歧", "市场分歧较大，减少操作，只观察Top1板块能否走持续", "red"
    else:
        regime, advice, color = "弱轮动", "有资金试探但不持续，多看少动，等待信号确认", "gray"

    return {
        "regime": regime,
        "advice": advice,
        "color": color,
        "rci_score": round(rci_score, 2),
        "components": {
            "dmi_score": dmi_val,
            "rpi_penalty": round(rpi_val * 0.6, 2),
            "north_bonus": round(north_net * 10, 2),
            "limitup_bonus": limit_up_count * 30,
        },
    }


def rank_industries(industries: list, top_n: int = 12) -> list:
    """按净流入排序的行业排行榜"""
    ranked = sorted(industries, key=lambda x: x.get("net_inflow", 0), reverse=True)

    result = []
    for i, ind in enumerate(ranked[:top_n]):
        inflow = ind.get("net_inflow", 0) or 0
        inflow_5d = ind.get("inflow_5d", 0) or 0
        dmi_est = max(0, inflow * 1.0 + max(0, inflow_5d) * 0.3)
        rpi_est = max(0, abs(inflow * 0.6) + max(0, -inflow_5d) * 0.2)

        if inflow > 50000:
            strength = "strong_inflow"
        elif inflow > 10000:
            strength = "mild_inflow"
        elif inflow > 0:
            strength = "weak_inflow"
        elif inflow > -10000:
            strength = "weak_outflow"
        else:
            strength = "strong_outflow"

        result.append({
            "rank": i + 1,
            "name": ind.get("name", ""),
            "dmi": round(dmi_est, 2),
            "rpi": round(rpi_est, 2),
            "net_inflow": round(inflow, 2),
            "inflow_5d": round(inflow_5d, 2),
            "price_pct": ind.get("price_pct", 0),
            "top_stock": ind.get("top_stock", ""),
            "top_stock_pct": ind.get("top_stock_pct", ""),
            "strength": strength,
        })

    return result


def daily_checklist(ranking: list, market_index: list = None,
                    north_flow: dict = None, limit_up: int = 0,
                    dmi: dict = None) -> list:
    """每日6项检查清单"""
    top3 = ranking[:3]
    bottom3 = ranking[-3:] if len(ranking) >= 3 else []

    top1_5d = ranking[0].get("inflow_5d", 0) if ranking else 0
    top1_name = ranking[0].get("name", "") if ranking else ""
    north_net = north_flow.get("net", 0) if north_flow else 0

    checklist = []

    # 1. 资金净买入
    buyers = [ind for ind in top3 if ind.get("net_inflow", 0) > 0]
    if buyers:
        names = "/".join(ind["name"] for ind in buyers[:2])
        checklist.append({"item": "资金净买入行业", "pass": True, "detail": f"{names} 等"})
    else:
        checklist.append({"item": "资金净买入行业", "pass": False, "detail": "无行业获主力净买入"})

    # 2. 资金净卖出
    sellers = [ind for ind in bottom3 if ind.get("net_inflow", 0) < 0]
    if sellers:
        names = "/".join(ind["name"] for ind in sellers[:2])
        checklist.append({"item": "资金净卖出行业", "pass": True, "detail": f"{names} 等"})
    else:
        checklist.append({"item": "资金净卖出行业", "pass": True, "detail": "无明显资金流出"})

    # 3. 5日Top1持续性
    has_5d = any(ind.get("inflow_5d", 0) != 0 for ind in ranking[:3])
    if not has_5d:
        checklist.append({"item": "5日Top1板块持续性", "pass": True,
                          "detail": f"{top1_name} — 5日数据待补充"})
    elif top1_5d > 0:
        checklist.append({"item": "5日Top1板块持续性", "pass": True,
                          "detail": f"{top1_name} 5日净流入 {top1_5d:.0f}万"})
    else:
        checklist.append({"item": "5日Top1板块持续性", "pass": False,
                          "detail": f"{top1_name} 5日为净流出"})

    # 4. 北向资金
    if north_net > 0:
        checklist.append({"item": "北向资金持续流入", "pass": True,
                          "detail": f"北向净流入 {north_net:.1f}亿"})
    else:
        checklist.append({"item": "北向资金持续流入", "pass": False,
                          "detail": f"北向净流出 {abs(north_net):.1f}亿" if north_net < 0 else "北向持平"})

    # 5. 涨停情绪
    if limit_up >= 40:
        checklist.append({"item": "涨停家数", "pass": True,
                          "detail": f"{limit_up}家涨停，市场情绪活跃"})
    elif limit_up >= 20:
        checklist.append({"item": "涨停家数", "pass": True,
                          "detail": f"{limit_up}家涨停，情绪一般"})
    else:
        checklist.append({"item": "涨停家数", "pass": False,
                          "detail": f"{limit_up}家涨停，情绪低迷"})

    # 6. 新板块崛起
    has_5d = any(ind.get("inflow_5d", 0) != 0 for ind in ranking[:5])
    if not has_5d:
        # 用今日流入强度粗略判断
        new_up = [ind for ind in ranking[:5]
                  if ind.get("net_inflow", 0) > 10000]
        if len(new_up) >= 3:
            names = "/".join(ind["name"] for ind in new_up[:3])
            checklist.append({"item": "新板块崛起信号", "pass": True,
                              "detail": f"{names} 今日资金大幅流入（5日数据待补充）"})
        else:
            checklist.append({"item": "新板块崛起信号", "pass": True,
                              "detail": "5日数据待补充，仅看今日——资金集中于科技方向"})
    else:
        new_up = [ind for ind in ranking[:5]
                  if ind.get("net_inflow", 0) > 0 and ind.get("inflow_5d", 0) > 0]
        if len(new_up) >= 2:
            names = "/".join(ind["name"] for ind in new_up[:3])
            checklist.append({"item": "新板块崛起信号", "pass": True,
                              "detail": f"{names} 出现资金持续流入"})
        else:
            checklist.append({"item": "新板块崛起信号", "pass": False,
                              "detail": "无明显新板块崛起"})

    return checklist


def extract_signals(ranking: list, dmi: dict = None) -> list:
    """提取热点信号"""
    signals = []
    has_5d_data = any(ind.get("inflow_5d", 0) != 0 for ind in ranking[:6])

    for ind in ranking[:6]:
        inflow = ind.get("net_inflow", 0)
        inflow_5d = ind.get("inflow_5d", 0) if has_5d_data else inflow  # fallback to 1d

        if inflow > 30000 and inflow_5d > 0:
            tp, note = "strong_inflow", "资金持续集中，主线热点"
        elif inflow > 10000 and inflow_5d > 0:
            tp, note = "mild_inflow", "资金温和流入，趋势向好"
        elif inflow > 0 and inflow_5d < 0:
            tp, note = "probing", "今日试探性流入，持续性待确认"
        elif inflow < -10000 and inflow_5d < 0:
            tp, note = "strong_outflow", "资金持续流出，回避"
        elif inflow < -5000:
            tp, note = "outflow_warn", "流出加大，注意风险"
        elif inflow > 0:
            tp, note = "inflow_today", "今日资金流入，待观察持续性"
        else:
            continue

        signals.append({"type": tp, "industry": ind["name"], "note": note})

    if dmi and dmi.get("dmi_net", 0) > 0:
        signals.append({"type": "overall_inflow", "industry": "全市场",
                        "note": f"主力资金整体净流入 {dmi['dmi_net']:.0f}万"})
    elif dmi:
        signals.append({"type": "overall_outflow", "industry": "全市场",
                        "note": f"主力资金整体净流出 {abs(dmi['dmi_net']):.0f}万"})

    return signals


# ═══════════════════════════════════════════════════════
# 截图新增功能：LDI / RFS / 热钱份额 / 题材对比 / 回流
# ═══════════════════════════════════════════════════════

#
# 新增: 推荐关注股 & 财报预警
# ═══════════════════════════════════════════════════════

WATCHLIST_PATH = None  # will be set relative to script dir

def _watchlist_path():
    """获取 watchlist JSON 文件路径"""
    if WATCHLIST_PATH:
        return WATCHLIST_PATH
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "_trade_watchlist.json")


def load_watchlist(path: str = None) -> list:
    """
    加载推荐关注股清单
    返回 [{name, code, reason, report_season, expected_report_date, ...}]
    """
    fp = path or _watchlist_path()
    if not os.path.exists(fp):
        # 默认内置清单
        return [
            {"name": "新易盛", "code": "300502", "reason": "AI光模块龙头",
             "report_season": "中报", "expected_report_date": "2026-08-28", "alert_before_days": 7},
            {"name": "中兴通讯", "code": "000063", "reason": "通信设备龙头",
             "report_season": "中报", "expected_report_date": "2026-08-30", "alert_before_days": 7},
        ]
    with open(fp, "r", encoding="utf-8") as f:
        return json.load(f)


def check_earnings_alerts(watchlist: list = None, today: str = None) -> dict:
    """
    检查财报预警 — 基于预期财报日期计算剩余天数

    返回: {
        "alerts": [ {name, code, days_left, level, message}, ... ],
        "upcoming": [...],  # 30天内
        "summary": "3只正常 | 1只临近 | 0只预警"
    }
    """
    from datetime import date, datetime

    if watchlist is None:
        watchlist = load_watchlist()

    if today is None:
        today = date.today()
    elif isinstance(today, str):
        today = date.fromisoformat(today)

    alerts = []
    upcoming = []

    for stock in watchlist:
        report_str = stock.get("expected_report_date", "")
        alert_days = stock.get("alert_before_days", 7)

        if not report_str:
            continue

        try:
            report_date = date.fromisoformat(report_str)
            days_left = (report_date - today).days
        except (ValueError, TypeError):
            continue

        name = stock.get("name", "")
        code = stock.get("code", "")
        season = stock.get("report_season", "财报")

        if days_left < 0:
            level = "🔴"
            message = f"{name}({code}) {season}已过{abs(days_left)}天，关注是否已披露"
        elif days_left == 0:
            level = "🔴"
            message = f"{name}({code}) 今日为{season}预计披露日！"
        elif days_left <= 3:
            level = "🔴"
            message = f"{name}({code}) {season}披露倒计时{days_left}天，即将进入窗口期"
        elif days_left <= alert_days:
            level = "🟡"
            message = f"{name}({code}) 距离{season}披露还有{days_left}天，进入关注窗口"
        elif days_left <= 30:
            level = "🟢"
            message = f"{name}({code}) 距离{season}披露还有{days_left}天，正常"
            upcoming.append({"name": name, "code": code, "days_left": days_left, "date": report_str})
        else:
            level = "🟢"
            message = f"{name}({code}) 距离{season}披露还有{days_left}天，正常"

        alerts.append({
            "name": name,
            "code": code,
            "season": season,
            "report_date": report_str,
            "days_left": days_left,
            "level": level,
            "message": message,
            "reason": stock.get("reason", ""),
        })

    # 排序：按剩余天数升序（最紧急的在前）
    alerts.sort(key=lambda x: x["days_left"])

    red_count = sum(1 for a in alerts if a["level"] == "🔴")
    yellow_count = sum(1 for a in alerts if a["level"] == "🟡")
    green_count = sum(1 for a in alerts if a["level"] == "🟢")

    totals = []
    if red_count:
        totals.append(f"{red_count}只预警")
    if yellow_count:
        totals.append(f"{yellow_count}只临近")
    if green_count:
        totals.append(f"{green_count}只正常")

    return {
        "alerts": alerts,
        "upcoming": sorted(upcoming, key=lambda x: x["days_left"])[:5],
        "summary": " | ".join(totals) if totals else "无数据",
        "check_date": today.isoformat(),
    }


def enrich_watchlist_with_flow(watchlist: list, industries: list) -> list:
    """
    将当前资金流数据与关注股关联 — 使用智能关键词匹配

    匹配策略:
    1. 个股→行业关键词映射表（精确匹配）
    2. 行业名包含个股名前两个字（如"通信"匹配"中兴通讯"）
    3. 个股名包含在行业名中或行业名中有关键词
    """
    # 个股→行业关键词映射表（可扩展）
    STOCK_INDUSTRY_MAP = {
        "新易盛": ["通信", "通信设备", "光模块", "CPO"],
        "中兴通讯": ["通信", "通信设备", "5G", "6G"],
        "亨通光电": ["通信", "通信设备", "光纤", "光通信", "光缆"],
        "生益科技": ["电子", "PCB", "半导体", "元件", "电子元器件"],
        "北方华创": ["电子", "半导体", "半导体设备", "芯片"],
        "沪硅产业": ["电子", "半导体", "硅片", "芯片材料"],
        "中芯国际": ["电子", "半导体", "芯片", "晶圆"],
        "宁德时代": ["电力设备", "电池", "新能源"],
        "比亚迪": ["汽车", "电力设备", "新能源车"],
        "贵州茅台": ["食品饮料", "白酒"],
        "中国平安": ["非银金融", "保险", "金融"],
        "招商银行": ["银行", "金融"],
        "东方财富": ["计算机", "软件", "金融科技"],
        "药明康德": ["医药生物", "医药", "医疗"],
        "迈瑞医疗": ["医药生物", "医疗", "医疗器械"],
        "紫金矿业": ["有色金属", "有色", "黄金", "矿业"],
        "万华化学": ["基础化工", "化工"],
        "海螺水泥": ["建筑材料", "水泥", "建材"],
        "美的集团": ["家用电器", "家电"],
        "海尔智家": ["家用电器", "家电"],
        "三一重工": ["机械设备", "机械", "工程机械"],
        "中国船舶": ["国防军工", "船舶", "军工"],
        "中航沈飞": ["国防军工", "航空", "军工"],
        "科大讯飞": ["计算机", "AI", "人工智能", "软件"],
        "金山办公": ["计算机", "软件"],
    }

    enriched = []
    for stock in watchlist:
        stock_name = stock.get("name", "")
        reason = stock.get("reason", "")

        # 匹配所属行业
        matched_ind = None
        match_method = None

        # 策略1: 关键词映射表
        keywords = STOCK_INDUSTRY_MAP.get(stock_name, [])
        if keywords and industries:
            for ind in industries:
                ind_name = ind.get("name", "")
                for kw in keywords:
                    if kw in ind_name:
                        matched_ind = ind
                        match_method = f"关键词'{kw}'→'{ind_name}'"
                        break
                if matched_ind:
                    break

        # 策略2: 个股名前两个字在行业名中
        if not matched_ind and industries:
            name_prefix = stock_name[:2]
            for ind in industries:
                ind_name = ind.get("name", "")
                if name_prefix in ind_name:
                    matched_ind = ind
                    match_method = f"前缀'{name_prefix}'→'{ind_name}'"
                    break

        # 策略3: 行业名包含个股名
        if not matched_ind and industries:
            for ind in industries:
                ind_name = ind.get("name", "")
                if stock_name in ind_name:
                    matched_ind = ind
                    match_method = f"全名匹配→'{ind_name}'"
                    break

        # 策略4: 反向——行业名的前两个字在个股名或理由中
        if not matched_ind and industries and reason:
            for ind in industries:
                ind_name = ind.get("name", "")
                ind_prefix = ind_name[:2] if ind_name else ""
                if ind_prefix and (ind_prefix in stock_name or ind_prefix in reason):
                    matched_ind = ind
                    match_method = f"行业前缀'{ind_prefix}'在理由中"
                    break

        if matched_ind:
            inflow = matched_ind.get("net_inflow", 0)
            price_pct = matched_ind.get("price_pct", 0)
            if inflow > 50000:
                flow_signal = "🟢 资金持续流入"
            elif inflow > 0:
                flow_signal = "🟢 小幅流入"
            elif inflow > -10000:
                flow_signal = "🟡 资金平衡"
            else:
                flow_signal = "🔴 资金流出"
        else:
            flow_signal = "⚪ 未匹配"
            price_pct = 0

        enriched.append({
            **stock,
            "flow_signal": flow_signal,
            "industry_pct": price_pct,
        })

    return enriched


# ═══════════════════════════════════════════════════════

def calc_ldi_ranking(industries: list, top_n: int = 10) -> list:
    """
    LDI = Liquidity Depth Index — 资金介入深度指数

    来源截图: "LDI，越高说明热钱介入越深"
    计算: 净流入金额×30% + 净流入/成交额比×25% + 超大+大单比例×25% + 5日持续性×20%

    注意: 输入需额外字段 turnover(成交额), super_large_ratio(超大单占比)
          缺失时自动降级为前4种已有指标的综合
    """
    ranked = sorted(industries, key=lambda x: x.get("net_inflow", 0), reverse=True)
    max_inflow = max((abs(ind.get("net_inflow", 0)) for ind in ranked), default=1)

    result = []
    for i, ind in enumerate(ranked[:top_n]):
        inflow = ind.get("net_inflow", 0) or 0
        inflow_5d = ind.get("inflow_5d", 0) or 0
        turnover = ind.get("turnover", 0) or 1

        # 流入强度分 (0-100)
        inflow_score = (inflow / max_inflow) * 100 if max_inflow > 0 else 0

        # 净流入/成交额比 (0-100)
        inflow_ratio = min(100, (abs(inflow) / turnover) * 1000)

        # 超大+大单比例 (如果没有则用净流入方向做调整)
        super_large = ind.get("super_large_ratio", 50)

        # 5日持续性
        persist = 50
        if inflow > 0 and inflow_5d > 0:
            persist = 80
        elif inflow > 0 and inflow_5d < 0:
            persist = 40  # 今日流入但5日流出 → 分歧中
        elif inflow < 0 and inflow_5d < 0:
            persist = 70  # 持续流出 → 深度一致
        elif inflow < 0 and inflow_5d > 0:
            persist = 30  # 今日逆转

        ldi_score = inflow_score * 0.30 + inflow_ratio * 0.25 + super_large * 0.25 + persist * 0.20

        if ldi_score >= 70:
            depth = "很深"
        elif ldi_score >= 45:
            depth = "较深"
        elif ldi_score >= 25:
            depth = "一般"
        else:
            depth = "浅"

        result.append({
            "rank": i + 1,
            "name": ind.get("name", ""),
            "ldi": round(ldi_score, 1),
            "depth": depth,
            "net_inflow": round(inflow, 2),
            "inflow_ratio": round(inflow_ratio, 1),
            "persist_score": round(persist, 1),
            "price_pct": ind.get("price_pct", 0),
        })

    return result


def calc_hot_money_share(industries: list) -> dict:
    """
    热钱份额分析 — 截图核心指标

    计算每个行业的净流入占全市场总净流入的比例
    判断热钱集中度: 是集中在 Top1-3 还是分散
    """
    total_positive = sum(
        ind.get("net_inflow", 0) for ind in industries
        if ind.get("net_inflow", 0) > 0
    )
    total = total_positive if total_positive > 0 else 1

    shares = []
    for ind in industries:
        inflow = ind.get("net_inflow", 0) or 0
        if inflow > 0:
            share = (inflow / total) * 100
            shares.append({
                "name": ind.get("name", ""),
                "net_inflow": round(inflow, 2),
                "share_pct": round(share, 1),
            })

    shares.sort(key=lambda x: x["share_pct"], reverse=True)

    # 集中度判断
    top3_share = sum(s["share_pct"] for s in shares[:3])
    if top3_share >= 60:
        concentration = "高度集中"
    elif top3_share >= 35:
        concentration = "中度集中"
    else:
        concentration = "分散"

    return {
        "total_inflow": round(total, 2),
        "top3_share": round(top3_share, 1),
        "concentration": concentration,
        "shares": shares[:8],
    }


def calc_rfs(industries: list, ldi_ranking: list = None) -> list:
    """
    RFS = Reflow Strength — 分歧后回流强度

    来源截图: "回流最强题材 RFS"
    思路: 在5日窗口内，如果某行业今天净流入且5日也为净流入 → 高回流强度
          如果今天净流入但5日净流出 → 分歧日，观察明天是否延续
    """
    result = []
    for ind in industries:
        inflow = ind.get("net_inflow", 0) or 0
        inflow_5d = ind.get("inflow_5d", 0) or 0

        if inflow == 0:
            continue

        # RFS = 今日流入强度 × 持续系数
        inflow_strength = abs(inflow)

        if inflow > 0 and inflow_5d > 0:
            # 持续流入 → 高RFS
            rfs = inflow_strength * 1.5
            signal = "strong_reflow"
            note = "资金持续回流，趋势确认"
        elif inflow > 0 and inflow_5d <= 0:
            # 分歧后首次回流 → 中RFS
            rfs = inflow_strength * 0.8
            signal = "reflow_trial"
            note = "分歧后试探性回流，待明日确认"
        elif inflow < 0 and inflow_5d < 0:
            # 持续流出
            rfs = inflow_strength * 0.3
            signal = "weak_outflow"
            note = "持续流出，无明显回流信号"
        elif inflow < 0 and inflow_5d >= 0:
            # 今日逆转
            rfs = -inflow_strength * 0.2
            signal = "outflow_warning"
            note = "今日资金转向流出，警惕"
        else:
            continue

        result.append({
            "name": ind.get("name", ""),
            "rfs": round(rfs, 2),
            "signal": signal,
            "note": note,
            "net_inflow": round(inflow, 2),
            "inflow_5d": round(inflow_5d, 2),
        })

    result.sort(key=lambda x: x["rfs"], reverse=True)
    return result[:8]


def compare_sectors(sector_a: str, sector_b: str, industries: list,
                    ldi_ranking: list = None, rfs_list: list = None) -> dict:
    """
    题材对比 — 截图"电力 vs 机器人"功能

    不是谁涨谁强，而是谁分歧后还能拿到钱。
    """
    def find_sector(name):
        for ind in industries:
            if name in ind.get("name", ""):
                return ind
        return None

    def find_ldi(name, ldi_list):
        if not ldi_list:
            return None
        for l in ldi_list:
            if name in l.get("name", ""):
                return l
        return None

    def find_rfs(name, rfs_list):
        if not rfs_list:
            return None
        for r in rfs_list:
            if name in r.get("name", ""):
                return r
        return None

    a = find_sector(sector_a)
    b = find_sector(sector_b)

    if not a and not b:
        return {"error": f"未找到 '{sector_a}' 和 '{sector_b}' 的数据"}
    if not a:
        return {"error": f"未找到 '{sector_a}' 的数据"}
    if not b:
        return {"error": f"未找到 '{sector_b}' 的数据"}

    a_ldi = find_ldi(sector_a, ldi_ranking)
    b_ldi = find_ldi(sector_b, ldi_ranking)
    a_rfs = find_rfs(sector_a, rfs_list)
    b_rfs = find_rfs(sector_b, rfs_list)

    def _pick(entry, key, default="N/A"):
        return entry.get(key, default) if entry else default

    a_net = a.get("net_inflow", 0) or 0
    b_net = b.get("net_inflow", 0) or 0
    a_5d = a.get("inflow_5d", 0) or 0
    b_5d = b.get("inflow_5d", 0) or 0

    # 谁分歧后还能拿到钱
    if a_net > 0 and b_net < 0:
        verdict = f"{sector_a} 明显优于 {sector_b}：资金净流入 vs 净流出"
    elif a_net < 0 and b_net > 0:
        verdict = f"{sector_b} 明显优于 {sector_a}：资金净流入 vs 净流出"
    elif a_net > 0 and a_5d > 0 and b_net > 0 and b_5d <= 0:
        verdict = f"{sector_a} 分歧后回流更强（5日持续流入，{sector_b}没有）"
    elif b_net > 0 and b_5d > 0 and a_net > 0 and a_5d <= 0:
        verdict = f"{sector_b} 分歧后回流更强（5日持续流入，{sector_a}没有）"
    elif a_net > 0 and b_net > 0:
        verdict = f"两者均流入，{sector_a}({a_net:.0f}万) vs {sector_b}({b_net:.0f}万)"
    else:
        verdict = f"两者均偏弱，{sector_a}({a_net:.0f}万) vs {sector_b}({b_net:.0f}万)"

    return {
        "sector_a": {
            "name": sector_a,
            "net_inflow": round(a_net, 2),
            "inflow_5d": round(a_5d, 2),
            "pct": a.get("price_pct", 0),
            "ldi": _pick(a_ldi, "ldi"),
            "rfs_signal": _pick(a_rfs, "signal"),
        },
        "sector_b": {
            "name": sector_b,
            "net_inflow": round(b_net, 2),
            "inflow_5d": round(b_5d, 2),
            "pct": b.get("price_pct", 0),
            "ldi": _pick(b_ldi, "ldi"),
            "rfs_signal": _pick(b_rfs, "signal"),
        },
        "verdict": verdict,
    }


def three_questions_review(ranking: list, ldi_ranking: list = None,
                           hot_money: dict = None, rfs_list: list = None) -> dict:
    """
    三件事复盘框架 — 截图核心复盘用法

    1. 钱今天去了哪里？
    2. 介入深不深？
    3. 分歧后回不回来？
    """
    top1 = ranking[0] if ranking else {}
    top2 = ranking[1] if len(ranking) > 1 else {}
    top3 = ranking[2] if len(ranking) > 2 else {}

    # Q1: 钱去了哪里？
    top_names = [ind["name"] for ind in ranking[:3] if ind.get("net_inflow", 0) > 0]
    if len(top_names) >= 2 and top_names[0] == top_names[1]:
        q1 = {"answer": f"资金高度集中于 {top_names[0]}，同一方向连续强势"}
    elif top_names:
        q1 = {"answer": f"资金主要流向 {', '.join(top_names[:2])}"}
    else:
        q1 = {"answer": "资金无明显集中方向"}

    # Q2: 介入深不深？
    if ldi_ranking and len(ldi_ranking) > 0:
        top_ldi = ldi_ranking[0].get("ldi", 0)
        if top_ldi >= 70:
            q2 = {"answer": f"介入很深 (LDI={top_ldi})，结合净流入/成交额看不是单纯脉冲"}
        elif top_ldi >= 45:
            q2 = {"answer": f"介入较深 (LDI={top_ldi})，有真实资金进场"}
        else:
            q2 = {"answer": f"介入一般 (LDI={top_ldi})，可能是跟风脉冲"}
    else:
        # 无LDI时用净流入和5日数据推断
        top1_5d = top1.get("inflow_5d", 0)
        top1_inflow = top1.get("net_inflow", 0)
        if top1_inflow > 50000 and top1_5d > 0:
            q2 = {"answer": "资金深度介入，5日持续流入"}
        elif top1_inflow > 50000:
            q2 = {"answer": f"今日流入{top1_inflow:.0f}万，但5日持续性待验证"}
        elif top1_inflow > 0:
            q2 = {"answer": f"今日温和流入，不算深"}
        else:
            q2 = {"answer": "资金未流入"}

    # Q3: 分歧后回不回来？
    if rfs_list and len(rfs_list) > 0:
        top_rfs = rfs_list[0]
        if top_rfs.get("signal") == "strong_reflow":
            q3 = {"answer": f"分歧后资金回流强 ({top_rfs['name']})，题材仍有生命力"}
        elif top_rfs.get("signal") == "reflow_trial":
            q3 = {"answer": f"分歧后有试探性回流 ({top_rfs['name']})，需明日确认是否续强"}
        else:
            q3 = {"answer": f"无明显回流信号，题材分歧后承接弱"}
    else:
        q3 = {"answer": "回流数据不足，需结合明日数据判断"}

    return {
        "q1": {"question": "钱今天去了哪里？", **q1},
        "q2": {"question": "介入深不深？", **q2},
        "q3": {"question": "分歧后回不回来？", **q3},
    }


# ═══════════════════════════════════════════════════════
# 新增: 板块强度评分系统（参考仪表盘PDF）
# ═══════════════════════════════════════════════════════

def calc_sector_strength_scores(industries: list, ranking: list = None) -> list:
    """
    板块强度评分系统（0-100分）

    参考PDF公式:
    评分 = 涨幅分×40% + 资金净流入分×25% + 持续性分×20% + 稳定性分×15%

    等级:
      82-100  极强
      68-81   强势
      52-67   震荡偏强
      38-51   震荡偏弱
      0-37    弱势
    """
    if not industries:
        return []
    if ranking is None:
        ranking = sorted(industries, key=lambda x: x.get("net_inflow", 0), reverse=True)

    inflows = [abs(i.get("net_inflow", 0)) for i in industries]
    pcts = [abs(i.get("price_pct", 0)) for i in industries]
    max_inflow = max(inflows, default=1)
    max_pct = max(pcts, default=1)

    results = []
    for ind in ranking:
        name = ind.get("name", "")
        inflow = ind.get("net_inflow", 0)
        pct = ind.get("price_pct", 0)
        inflow_5d = ind.get("inflow_5d", 0)
        turnover = ind.get("turnover", 0)

        # 1. 涨幅分 (40%)
        pct_score = min(100, (abs(pct) / max(max_pct, 0.01)) * 100)
        if pct < 0:
            pct_score *= 0.3

        # 2. 资金净流入分 (25%)
        if inflow > 0:
            inflow_score = min(100, (inflow / max(max_inflow, 1)) * 100)
        else:
            inflow_score = min(100, (abs(inflow) / max(max_inflow, 1)) * 100) * 0.3

        # 3. 持续性分 (20%)
        if inflow > 0 and inflow_5d > 0:
            persist_score = 80 + min(20, (inflow_5d / max(max_inflow, 1)) * 20)
        elif inflow > 0 and inflow_5d <= 0:
            persist_score = 50
        elif inflow < 0 and inflow_5d < 0:
            persist_score = 40
        elif inflow < 0 and inflow_5d >= 0:
            persist_score = 30
        else:
            persist_score = 50

        # 4. 稳定性分 (15%)
        if turnover > 0 and abs(inflow) > 0:
            ratio = abs(inflow) / turnover
            stability_score = min(100, ratio * 500)
        else:
            stability_score = 70 if (inflow > 0 and inflow_5d > 0) else (50 if inflow > 0 else 40)

        total = round(pct_score * 0.40 + inflow_score * 0.25 + persist_score * 0.20 + stability_score * 0.15, 1)

        if total >= 82:
            level = "极强"
        elif total >= 68:
            level = "强势"
        elif total >= 52:
            level = "震荡偏强"
        elif total >= 38:
            level = "震荡偏弱"
        else:
            level = "弱势"

        results.append({
            "name": name, "score": total, "level": level,
            "components": {"pct": round(pct_score, 1), "inflow": round(inflow_score, 1),
                           "persist": round(persist_score, 1), "stability": round(stability_score, 1)},
            "net_inflow": inflow, "price_pct": pct,
        })

    results.sort(key=lambda x: x["score"], reverse=True)
    return results


def gen_dashboard_data(scores: list) -> dict:
    """生成仪表盘摘要"""
    top3 = scores[:3] if scores else []
    strong = [s for s in scores if s["score"] >= 68]
    weak = [s for s in scores if s["score"] < 38]
    return {
        "top_sectors": top3,
        "strong_count": len(strong),
        "weak_count": len(weak),
        "total_sectors": len(scores),
    }


# ═══════════════════════════════════════════════════════

def run_analysis(data: dict) -> dict:
    """接收外部数据，执行完整分析，返回结果"""

    industries = data.get("industries", [])
    market_index = data.get("market_index", [])
    north_flow = data.get("north_flow", {})
    limit_up = data.get("limit_up_count", 0)
    limit_down = data.get("limit_down_count", 0)
    lianban_count = data.get("lianban_count", 0)
    max_lianban = data.get("max_lianban", 0)
    zhaban_count = data.get("zhaban_count", 0)

    north_net = north_flow.get("net", 0) if isinstance(north_flow, dict) else 0

    dmi = calc_dmi(industries, lianban_count)
    rpi = calc_rpi(industries, zhaban_count, max_lianban)
    rci = calc_rci(dmi, rpi, north_net, limit_up, dmi.get("dmi_net", 0))
    ranking = rank_industries(industries, top_n=12)
    checklist = daily_checklist(ranking, market_index, north_flow, limit_up, dmi)
    signals = extract_signals(ranking, dmi)

    # 截图新增功能
    ldi_ranking = calc_ldi_ranking(industries, top_n=10)
    hot_money = calc_hot_money_share(industries)
    rfs_list = calc_rfs(industries, ldi_ranking)
    three_q = three_questions_review(ranking, ldi_ranking, hot_money, rfs_list)

    # 默认题材对比（取流入第一和流出第一，让用户可指定）
    top_inflow_name = ranking[0]["name"] if ranking else ""
    top_outflow_name = ranking[-1]["name"] if ranking else ""
    default_compare = compare_sectors(top_inflow_name, top_outflow_name,
                                       industries, ldi_ranking, rfs_list)

    # 推荐关注股 & 财报预警
    watchlist = load_watchlist()
    watchlist_enriched = enrich_watchlist_with_flow(watchlist, industries)
    earnings_alerts = check_earnings_alerts(watchlist)

    # 板块强度评分（仪表盘）
    sector_scores = calc_sector_strength_scores(industries, ranking)
    dashboard = gen_dashboard_data(sector_scores)

    return {
        "version": VERSION,
        "date": date.today().isoformat(),
        "indicators": {"dmi": dmi, "rpi": rpi, "rci": rci},
        "ranking": ranking,
        "checklist": checklist,
        "signals": signals,
        "ldi_ranking": ldi_ranking,
        "hot_money": hot_money,
        "rfs_ranking": rfs_list,
        "three_questions": three_q,
        "compare": default_compare,
        "watchlist": watchlist_enriched,
        "earnings_alerts": earnings_alerts,
        "sector_scores": sector_scores,
        "dashboard": dashboard,
        "summary": {
            "regime": rci["regime"],
            "advice": rci["advice"],
            "main_line": ranking[0]["name"] if ranking else "",
            "limit_up_total": limit_up,
            "lianban_total": lianban_count,
        },
    }


# ═══════════════════════════════════════════════════════
# CLI 入口
# ═══════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description=f"A股短线量化追踪系统 {VERSION}")
    parser.add_argument("--data", type=str, help="JSON 格式的输入数据")
    parser.add_argument("--stdin", action="store_true", help="从 stdin 读取 JSON")
    parser.add_argument("--auto", action="store_true", help="尝试自动获取数据（可能失败）")
    parser.add_argument("--report", action="store_true", help="输出格式化报告（文本）")
    parser.add_argument("--rank", action="store_true", help="仅输出行业排行榜")
    parser.add_argument("--checklist", action="store_true", help="仅输出每日检查清单")
    parser.add_argument("--regime", action="store_true", help="仅输出市场格局判断")
    parser.add_argument("--ldi", action="store_true", help="仅输出LDI资金介入深度排名")
    parser.add_argument("--hotmoney", action="store_true", help="仅输出热钱份额分析")
    parser.add_argument("--rfs", action="store_true", help="仅输出回流强度排名")
    parser.add_argument("--compare", type=str, help="对比两个题材，格式 '题材A|题材B'")
    parser.add_argument("--threeq", action="store_true", help="仅输出三件事复盘框架")
    parser.add_argument("--watchlist", action="store_true", help="查看推荐关注股清单")
    parser.add_argument("--watchlist-alerts", action="store_true", help="查看财报预警")
    parser.add_argument("--add-watch", type=str, help="添加关注股, 格式 '名称,代码,理由'")
    args = parser.parse_args()

    data = None

    if args.data:
        data = json.loads(args.data)
    elif args.stdin:
        data = json.loads(sys.stdin.read())
    elif args.auto:
        # 尝试从 API 获取（可能失败）
        _try_fetch = _make_fetcher()
        data = _try_fetch() if _try_fetch else None
        if not data:
            print('{"error": "auto_fetch_failed", "msg": "无法从数据源获取数据，请使用 --data 传入或通过 stdin 输入"}')
            sys.exit(1)
    else:
        # 默认：输出说明 + 返回空分析骨架
        print(json.dumps({
            "info": f"A股短线量化追踪系统 {VERSION}",
            "usage": {
                "auto_mode": "python _trade_agent.py --auto",
                "stdin_mode": "echo '...' | python _trade_agent.py --stdin",
                "data_mode": "python _trade_agent.py --data '<json>'",
            },
            "input_schema": {
                "industries": [{"name": "str", "net_inflow": "float(万)", "inflow_5d": "float(万)", "price_pct": "float", "top_stock": "str"}],
                "market_index": [{"name": "str", "price": "float", "pct": "float"}],
                "north_flow": {"net": "float(亿)"},
                "limit_up_count": "int",
                "limit_down_count": "int",
                "lianban_count": "int",
                "max_lianban": "int",
            },
        }, ensure_ascii=False, indent=2))
        return

    result = run_analysis(data)

    if args.rank:
        print(json.dumps(result.get("ranking", []), ensure_ascii=False, indent=2))
    elif args.checklist:
        print(json.dumps(result.get("checklist", []), ensure_ascii=False, indent=2))
    elif args.regime:
        print(json.dumps(result.get("indicators", {}).get("rci", {}), ensure_ascii=False, indent=2))
    elif args.ldi:
        print(json.dumps(result.get("ldi_ranking", []), ensure_ascii=False, indent=2))
    elif args.hotmoney:
        print(json.dumps(result.get("hot_money", {}), ensure_ascii=False, indent=2))
    elif args.rfs:
        print(json.dumps(result.get("rfs_ranking", []), ensure_ascii=False, indent=2))
    elif args.compare:
        parts = args.compare.split("|")
        if len(parts) == 2:
            sa, sb = parts[0].strip(), parts[1].strip()
            cmp = compare_sectors(sa, sb, data.get("industries", []), result.get("ldi_ranking"), result.get("rfs_ranking"))
            print(json.dumps(cmp, ensure_ascii=False, indent=2))
        else:
            print(json.dumps({"error": "格式错误，使用 --compare '题材A|题材B'"}, ensure_ascii=False, indent=2))
    elif args.threeq:
        print(json.dumps(result.get("three_questions", {}), ensure_ascii=False, indent=2))
    elif args.watchlist:
        wl = load_watchlist()
        inds = data.get("industries", []) if data else []
        enriched = enrich_watchlist_with_flow(wl, inds)
        print(json.dumps(enriched, ensure_ascii=False, indent=2))
    elif args.watchlist_alerts:
        alerts = check_earnings_alerts()
        print(json.dumps(alerts, ensure_ascii=False, indent=2))
    elif args.add_watch:
        parts = args.add_watch.split(",")
        if len(parts) >= 2:
            wl = load_watchlist()
            new_stock = {
                "name": parts[0].strip(),
                "code": parts[1].strip(),
                "reason": parts[2].strip() if len(parts) >= 3 else "",
                "report_season": "中报",
                "expected_report_date": "",
                "alert_before_days": 7,
            }
            wl.append(new_stock)
            fp_w = _watchlist_path()
            with open(fp_w, "w", encoding="utf-8") as f:
                json.dump(wl, f, ensure_ascii=False, indent=2)
            print(json.dumps({"status": "ok", "added": new_stock, "total": len(wl)}, ensure_ascii=False, indent=2))
        else:
            print(json.dumps({"error": "格式错误, 使用 --add-watch '名称,代码,理由'"}, ensure_ascii=False, indent=2))
    elif args.report:
        print(json.dumps(result, ensure_ascii=False))
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))


# ── 自动获取（备用，含东财API） ─────────────────────

def _make_fetcher():
    """尝试创建数据获取器，依赖可用时返回 fetcher 函数"""
    try:
        import urllib.request, ssl
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

        def _fetch(url):
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Referer": "https://data.eastmoney.com/",
            }
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=15, context=ctx) as r:
                return json.loads(r.read().decode("utf-8"))

        def fetcher():
            """从东财API获取数据"""
            # 行业资金流
            url_ind = (
                "https://push2.eastmoney.com/api/qt/clist/get"
                "?pn=1&pz=60&po=1&np=1"
                "&fields=f12,f14,f2,f3,f4,f62,f66,f69,f72,f78,f84,f124,f204,f205"
                "&fid=f62"
                "&fs=m:90+t:2+f:!50"
                "&ut=bd1d9ddb04089700cf9c27f6f7426281"
            )
            raw = _fetch(url_ind)
            industries = []
            for row in raw.get("data", {}).get("diff", []):
                industries.append({
                    "name": row.get("f14", ""),
                    "net_inflow": (row.get("f62", 0) or 0),
                    "inflow_5d": (row.get("f78", 0) or 0),
                    "price_pct": (row.get("f3", 0) or 0),
                    "top_stock": row.get("f205", "") or "",
                    "top_stock_pct": row.get("f204", "") or "",
                })

            # 大盘指数
            try:
                url_idx = (
                    "https://push2.eastmoney.com/api/qt/ulist.np/get"
                    "?fltt=2&fields=f2,f3,f4,f12,f14"
                    "&secids=1.000001,0.399001,0.399006,0.000688,0.399300"
                    "&ut=bd1d9ddb04089700cf9c27f6f7426281"
                )
                idx_raw = _fetch(url_idx)
                market_index = []
                for row in idx_raw.get("data", {}).get("diff", []):
                    market_index.append({
                        "name": row.get("f14", ""),
                        "price": row.get("f2", 0),
                        "pct": row.get("f3", 0),
                    })
            except Exception:
                market_index = []

            return {
                "industries": industries,
                "market_index": market_index,
                "north_flow": {},
                "limit_up_count": 0,
                "limit_down_count": 0,
                "lianban_count": 0,
                "max_lianban": 0,
                "_source": "eastmoney_api",
            }

        return fetcher
    except Exception:
        return None


if __name__ == "__main__":
    main()
