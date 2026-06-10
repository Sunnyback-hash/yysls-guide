#!/usr/bin/env python3
"""
板块强度评分分析引擎 — 完整匹配参考PDF
评分 = 涨停散40% + 成交额/容量25% + 辨识度20% + 承接/换手15%
"""
from datetime import date, datetime
import os, json, math

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ═══════════════════════════════════════════════════
# 常量
# ═══════════════════════════════════════════════════

# 板块效应关键词映射表 (行业名 → 参考PDF标准化板块名)
SECTOR_ALIASES = {
    "电子": "半导体/存储/MLCC", "半导体": "半导体/存储/MLCC",
    "元件": "半导体/存储/MLCC", "MLCC": "半导体/存储/MLCC",
    "存储": "半导体/存储/MLCC", "芯片": "半导体/存储/MLCC",
    "通信": "CPO/光模块/通信", "光模块": "CPO/光模块/通信",
    "光通信": "CPO/光模块/通信", "CPO": "CPO/光模块/通信",
    "光纤": "CPO/光模块/通信", "光缆": "CPO/光模块/通信",
    "PCB": "PCB/玻纤布/覆铜板", "玻纤": "PCB/玻纤布/覆铜板",
    "覆铜板": "PCB/玻纤布/覆铜板",
    "AI应用": "AI应用/大模型", "大模型": "AI应用/大模型",
    "机器人": "机器人/人形AI", "人形": "机器人/人形AI",
    "有色": "有色/稀土/能源金属", "稀土": "有色/稀土/能源金属",
    "新能源金属": "有色/稀土/能源金属",
    "储能": "储能/风光协同", "风光": "储能/风光协同",
    "电力设备": "储能/风光协同", "光伏": "储能/风光协同",
    "煤炭": "煤炭/传统能源", "传统能源": "煤炭/传统能源",
    "白酒": "白酒消费", "消费": "白酒消费",
    "石油": "石油石化", "石化": "石油石化",
    "医药": "医药/医疗", "医疗": "医药/医疗",
    "汽车": "汽车/零部件", "零部件": "汽车/零部件",
    "食品饮料": "白酒消费", "传媒": "文化传媒",
    "计算机": "计算机/信创",
}

# 龙头候选股 (板块名拼音首字母 → 候选股列表)
DEFAULT_LEADERS = {
    "半导体/存储/MLCC": ["沪硅产业", "华大九天", "太极实业", "紫光国微"],
    "PCB/玻纤布/覆铜板": ["金安国纪", "同益股份", "生益科技", "兴森科技"],
    "有色/稀土/能源金属": ["盛和资源", "华迁新材", "嘉元科技", "北方稀土"],
    "CPO/光模块/通信": ["天洋新材", "泰和新材", "长飞光纤", "亨通光电", "新易盛"],
    "AI应用/大模型": ["汉王科技", "格灵深瞳", "科大讯飞"],
    "机器人/人形AI": ["埃斯顿", "埃夫特", "拓斯达"],
    "储能/风光协同": ["豫能控股", "明阳智能", "阳光电源"],
    "煤炭/传统能源": ["大有能源", "中国神华", "陕西煤业"],
    "白酒消费": ["贵州茅台", "五粮液", "山西汾酒"],
    "石油石化": ["中国石化", "中国石油", "上海石化"],
}

# 板块综合评级
RATING_LEVELS = {
    "A+": "核心主线，资金深度介入",
    "A": "强势主线，辨识度高",
    "A-": "轮动主线，需承接确认",
    "B+": "支线活跃，局部机会",
    "B": "支线试探，持续性弱",
    "C": "跟风反弹，无板块效应",
    "回避": "资金持续流出，回避",
}


# ═══════════════════════════════════════════════════
# 核心评分函数
# ═══════════════════════════════════════════════════

def normalize_sector_name(raw_name):
    """将原始行业名映射为标准板块名"""
    for kw, standard in SECTOR_ALIASES.items():
        if kw in raw_name:
            return standard
    return raw_name


def calc_composite_score(industry, limit_up_count=0, lianban_count=0,
                         top1_freq=0, context_sectors=None):
    """
    计算板块综合强度 (0-100)

    评分 = 涨停/连板散40% + 成交额/容量25% + 辨识度20% + 承接/换手15%

    输入: 行业单条数据
    返回: {score, components}
    """
    inflow = industry.get("net_inflow", 0) or 0
    pct = industry.get("price_pct", 0) or 0
    turnover = industry.get("turnover", 0) or 1
    inflow_5d = industry.get("inflow_5d", 0) or 0
    super_large = industry.get("super_large_ratio", 50) or 50
    is_top = industry.get("_is_top1", False)
    top1_count = industry.get("_top1_days", 0)

    # ── 1. 涨停/连板散分 (40%) ──
    # 用涨跌幅 + 资金强度 + 个股异动来代理
    pct_score = min(100, max(0, (abs(pct) / 10) * 100))  # 设定10%涨停为满分
    inflow_pct = min(100, max(0, (inflow / max(300000, 1)) * 100))
    if inflow < 0:
        inflow_pct *= 0.3
    explosive_score = pct_score * 0.5 + inflow_pct * 0.5
    # 如果当日涨停多(+10%), 给高分
    if pct >= 5:
        explosive_score = min(100, explosive_score * 1.3)
    sorce1 = min(100, explosive_score)

    # ── 2. 成交额/容量分 (25%) ──
    # 成交额越大越好，用主力净流入占成交额比例
    cap_ratio = abs(inflow) / turnover * 1000
    cap_score = min(100, cap_ratio * 0.8)
    if inflow < 0:
        cap_score *= 0.4  # 流出时容量分打折
    sorce2 = min(100, cap_score)

    # ── 3. 辨识度分 (20%) ──
    # Top1频率高、超大单比例高、领涨股明显
    recog_score = 50  # 默认
    if is_top:
        recog_score += 20
    if top1_count >= 3:
        recog_score += 15
    if super_large >= 60:
        recog_score += 15
    elif super_large >= 40:
        recog_score += 5
    sorce3 = min(100, recog_score)

    # ── 4. 承接/换手分 (15%) ──
    # 净流入为正+成交活跃 = 有承接
    if inflow > 0:
        absorb_score = 60
        if inflow_5d > 0:
            absorb_score += 20  # 持续流入
        if cap_ratio > 0.05:
            absorb_score += 20  # 换手活跃
    else:
        absorb_score = 30
        if inflow_5d < -50000:
            absorb_score = 20
    sorce4 = min(100, absorb_score)

    total = round(sorce1 * 0.40 + sorce2 * 0.25 + sorce3 * 0.20 + sorce4 * 0.15, 1)
    return {
        "score": total,
        "components": {
            "explosive": round(sorce1, 1),
            "capacity": round(sorce2, 1),
            "recognition": round(sorce3, 1),
            "absorption": round(sorce4, 1),
        },
    }


def get_stage_label(score, inflow=None, inflow_5d=None):
    """阶段分类"""
    if score >= 82:
        return "强趋/高潮"
    if score >= 68:
        return "强势主升"
    if score >= 52:
        return "震荡/修复"
    if score >= 38:
        return "弱势观察"
    return "退出/回避"


def get_sector_effect(score, inflow, inflow_5d):
    """板块效应分类"""
    if score >= 80 and inflow > 0:
        return "强修复"
    if score >= 68 and inflow > 0:
        return "跟风散/观望"
    if score >= 38 and inflow_5d < 0 and inflow < 0:
        return "等待"
    if score < 38:
        return "无板块效应"
    return "跟风散/观望"


def get_sector_rating(score, effect, inflow):
    """综合评级: A+/A/A-/B+/B/C/回避"""
    if score >= 85 and effect == "强修复":
        return "A+"
    if score >= 75 and (effect == "强修复" or effect == "跟风散/观望"):
        return "A"
    if score >= 65 and inflow > 0:
        return "A-"
    if score >= 52 and inflow > 0:
        return "B+"
    if score >= 38:
        return "B"
    if score >= 20:
        return "C"
    return "回避"


def get_structure_type(score, inflow, effect):
    """结构分类: 主升/研究/杂毛"""
    if score >= 80 and inflow > 30000:
        return "主升"
    if score >= 52 and inflow > 0:
        return "研究"
    return "杂毛"


def find_leading_stocks(sector_name, industry_data, top_stocks_info=None):
    """
    为板块匹配龙头候选股
    优先从领涨股中取，否则从默认映射表取
    """
    # 先从默认映射表
    for kw, leaders in DEFAULT_LEADERS.items():
        if kw in sector_name or sector_name in kw:
            return leaders[:3]

    # 从行业数据中取top_stock
    top = industry_data.get("top_stock", "")
    if top:
        return [top]
    return []


# ═══════════════════════════════════════════════════
# 完整分析
# ═══════════════════════════════════════════════════

def analyze_sectors(industries, limit_up_count=0, lianban_count=0,
                    market_index=None, north_flow=None):
    """
    入口函数: 对全行业执行完整评分分析
    返回匹配参考PDF格式的结构化数据
    """
    if not industries:
        return {"sectors": [], "summary": {}}

    # 先找出Top1出现次数的近似值 (用净流入排序判断)
    sorted_inds = sorted(industries, key=lambda x: x.get("net_inflow", 0), reverse=True)
    top1_days_map = {}
    if sorted_inds:
        top1_days_map[sorted_inds[0].get("name", "")] = 5  # 假设第一名为5日Top1

    results = []
    for idx, ind in enumerate(sorted_inds):
        name = ind.get("name", "")
        standard_name = normalize_sector_name(name)
        inflow = ind.get("net_inflow", 0) or 0
        pct = ind.get("price_pct", 0) or 0
        inflow_5d = ind.get("inflow_5d", 0) or 0

        # 标记是否为当前 Top1
        ind["_is_top1"] = (idx == 0)
        ind["_top1_days"] = top1_days_map.get(name, 0)

        cs = calc_composite_score(ind, limit_up_count, lianban_count,
                                   top1_days_map.get(name, 0), sorted_inds)
        score = cs["score"]
        stage = get_stage_label(score, inflow, inflow_5d)
        effect = get_sector_effect(score, inflow, inflow_5d)
        rating = get_sector_rating(score, effect, inflow)
        struct = get_structure_type(score, inflow, effect)

        # 龙头候选
        leaders = find_leading_stocks(standard_name, ind)

        # 日变化 (用5日+今日净流入推算趋势变化)
        daily_change = 0
        if inflow_5d != 0:
            trend_ratio = inflow / max(abs(inflow_5d), 1)
            daily_change = round(trend_ratio * 10)  # 粗估变化值
        else:
            daily_change = round(inflow / 100000)  # 用净流入量级

        results.append({
            "name": standard_name,
            "raw_name": name,
            "score": score,
            "components": cs["components"],
            "stage": stage,
            "effect": effect,
            "rating": rating,
            "structure": struct,
            "daily_change": daily_change,
            "trend_5d": round(inflow_5d / 10000, 1) if abs(inflow_5d) > 0 else 0,
            "net_inflow": inflow,
            "price_pct": pct,
            "leaders": leaders,
            "turnover": ind.get("turnover", 0),
        })

    # 强度升降排名
    gainers = [r for r in results if r["daily_change"] > 0]
    gainers.sort(key=lambda x: x["daily_change"], reverse=True)
    decliners = [r for r in results if r["daily_change"] < 0]
    decliners.sort(key=lambda x: x["daily_change"])

    # 合并同名标准板块
    merged = {}
    for r in results:
        n = r["name"]
        if n in merged:
            old = merged[n]
            if r["score"] > old["score"]:
                merged[n] = r
        else:
            merged[n] = r
    merged_list = sorted(merged.values(), key=lambda x: x["score"], reverse=True)

    # 统计
    strong = [r for r in merged_list if r["score"] >= 68]
    weak = [r for r in merged_list if r["score"] < 38]

    # 综合评级分布
    rating_dist = {}
    for r in merged_list:
        rt = r["rating"]
        rating_dist[rt] = rating_dist.get(rt, 0) + 1

    north_net = north_flow.get("net", 0) if north_flow else 0

    return {
        "sectors": merged_list,
        "raw_sectors": results,
        "gainers": gainers[:5],
        "decliners": decliners[:5],
        "summary": {
            "total": len(merged_list),
            "strong_count": len(strong),
            "weak_count": len(weak),
            "top_score": merged_list[0]["score"] if merged_list else 0,
            "top_sector": merged_list[0]["name"] if merged_list else "",
            "north_net": north_net,
            "rating_distribution": rating_dist,
        },
        "market_regime": "轮动",
    }


def filter_by_rating(sectors, min_rating="B"):
    """按最低评级过滤"""
    order = ["A+", "A", "A-", "B+", "B", "C", "回避"]
    min_idx = order.index(min_rating) if min_rating in order else 4
    return [s for s in sectors if s["rating"] in order and order.index(s["rating"]) <= min_idx]


# ═══════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════

if __name__ == "__main__":
    import sys
    data_file = os.path.join(BASE_DIR, "_pdf_result.json")
    if not os.path.exists(data_file):
        # 尝试从stdin读取
        try:
            raw = sys.stdin.read()
            data = json.loads(raw)
        except:
            print("请先运行 trade_agent 生成 _pdf_result.json")
            sys.exit(1)
    else:
        with open(data_file, "r", encoding="utf-8") as f:
            data = json.load(f)

    industries = data.get("industries", [])
    limit_up = data.get("limit_up_count", 0)
    lianban = data.get("lianban_count", 0)
    result = analyze_sectors(industries, limit_up, lianban)

    print(json.dumps(result, ensure_ascii=False, indent=2))
