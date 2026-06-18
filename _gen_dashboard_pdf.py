#!/usr/bin/env python3
"""
智能板块强度仪表盘 PDF v3 — 极简稳定版
横版A4, 无复杂分页, 每页自包含
"""
import json, os, sys
BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
from _sector_analysis import analyze_sectors
from fpdf import FPDF

FONT = r"C:\Windows\Fonts\simhei.ttf"
LM = 34
RED = (200,55,50); BLUE = (0,95,145); GREEN = (100,160,100)
NAVY = (20,40,75); TEAL = (0,110,130)
G_D = (55,55,55); G_M = (130,130,130); G_L = (200,200,200)

class P(FPDF):
    def __init__(self):
        super().__init__("L","mm","A4")
        self.add_font("zh","",FONT); self.add_font("zh","B",FONT)
        self.set_auto_page_break(False); self.set_margins(0,0,0)

def sc(s):
    if s>=82: return RED
    if s>=68: return (220,110,40)
    if s>=52: return BLUE
    if s>=38: return (120,130,140)
    return GREEN

def rc(r):
    return {"A+":RED,"A":(220,110,40),"A-":TEAL,"B+":BLUE,"B":G_M,"C":G_L,"回避":GREEN}.get(r,G_M)

def build(data, out):
    pdf = P()
    inds = data.get("industries",[])
    idx = data.get("market_index",[])
    nf = data.get("north_flow",{})
    lu = data.get("limit_up_count",0)
    sa = analyze_sectors(inds, lu, data.get("lianban_count",0), idx, nf)
    secs = sa["sectors"]
    gainers = sa["gainers"]; decliners = sa["decliners"]

    def add_hdr(ti):
        pdf.add_page()
        pdf.set_fill_color(*NAVY)
        pdf.rect(0,0,297,48,"F")
        pdf.set_xy(LM,8)
        pdf.set_font("zh","B",14); pdf.set_text_color(*TEAL)
        pdf.cell(400,7,ti)
        pdf.set_xy(LM,20)
        pdf.set_font("zh","",8); pdf.set_text_color(*G_M)
        pdf.cell(200,5,"2026-06-09 周二 | 最近14个交易日 (05-21 ~ 06-09)")
        pdf.set_xy(LM,30)
        pdf.set_font("zh","",7); pdf.set_text_color(*G_M)
        pdf.set_text_color(*RED); pdf.cell(50,4,"红=强/上涨/流入")
        pdf.set_text_color(*BLUE); pdf.cell(50,4,"蓝=观察/试探")
        pdf.set_text_color(*GREEN); pdf.cell(50,4,"绿=弱/下跌/流出")

    def body(t, sz=7):
        pdf.set_font("zh","",sz); pdf.set_text_color(*G_D)
        pdf.multi_cell(740,4,t)
        pdf.ln(2)

    def kv(k,v,k2=None,v2=None):
        pdf.set_font("zh","B",7); pdf.set_text_color(*G_D)
        w = pdf.get_string_width(k+" ")+2
        pdf.cell(w,5,k)
        pdf.set_font("zh","",7); pdf.set_text_color(*TEAL)
        pdf.cell(80-w,5,v)
        if k2:
            pdf.set_font("zh","B",7); pdf.set_text_color(*G_D)
            w2 = pdf.get_string_width(k2+" ")+2
            pdf.cell(w2,5,k2)
            pdf.set_font("zh","",7); pdf.set_text_color(*TEAL)
            pdf.cell(200,5,v2)
        pdf.ln(5.5)

    # ═══════════════ P1: 封面 ═══════════════
    pdf.add_page()
    pdf.set_fill_color(*NAVY); pdf.rect(0,0,297,95,"F")
    pdf.set_xy(LM,25)
    pdf.set_font("zh","B",28); pdf.set_text_color(*TEAL)
    pdf.cell(400,12,"智能板块强度仪表盘")
    pdf.set_xy(LM,45)
    pdf.set_font("zh","",11); pdf.set_text_color(*G_M)
    pdf.cell(400,7,"2026-06-09 周二 | 最近14个交易日 (2026-05-21 ~ 2026-06-09)")
    pdf.set_xy(LM,62)
    pdf.set_font("zh","B",9); pdf.set_text_color(*TEAL)
    s0 = secs[0] if secs else {}
    pdf.cell(400,6,f"核心结论: {s0.get('name','')}全线强修复, {sa['summary']['strong_count']}个板块进入强势区间")
    # 指数
    y0=105
    for i,(n,v,s) in enumerate([("上证","4010+1.28%","收复4000点"),("深成指","15268+3.02%","科技权重带动"),("创业板","3961+3.93%","成长风格活跃"),("涨停",f"{lu}家","封板率84%")]):
        x=LM+i*185
        pdf.set_xy(x,y0); pdf.set_font("zh","B",9); pdf.set_text_color(*NAVY); pdf.cell(170,5,n)
        pdf.set_xy(x,y0+8); pdf.set_font("zh","B",13); pdf.set_text_color(*RED); pdf.cell(170,6,v)
        pdf.set_xy(x,y0+16); pdf.set_font("zh","",7); pdf.set_text_color(*G_M); pdf.cell(170,4,s)
    # 第一梯队
    pdf.set_xy(LM,y0+35)
    pdf.set_font("zh","B",8); pdf.set_text_color(*NAVY); pdf.cell(200,5,"第一执行梯队")
    strong = [s for s in secs if s["score"]>=68][:6]
    for i,s in enumerate(strong):
        col=i//3; row=i%3
        x=LM+col*380; y=y0+45+row*22
        pdf.set_xy(x+5,y); pdf.set_font("zh","B",7)
        pdf.set_text_color(*sc(s["score"])); pdf.cell(180,5,f"[{s['rating']}] {s['name']}")
        pdf.set_font("zh","",6.5); pdf.set_text_color(*G_M)
        pdf.cell(200,5,", ".join(s.get("leaders",[])[:2]))

    # ═══════════════ P2: 使用说明+评分体系 ═══════════════
    add_hdr("使用说明 & 评分体系")
    body("为什么用颜色? A股投资者习惯以颜色判断强弱——红=强、涨、流入；蓝=观察、试探；绿=弱、跌、流出。")
    body("综合强度评分公式: 评分 = (涨停/连板散)40% + (成交额/容量)25% + (辨识度)20% + (承接/换手)15%")
    body("涨停/连板散: 涨跌幅+净流入强度 | 成交额/容量: 净流入占成交额比 | 辨识度: Top1频率+超大单比 | 承接/换手: 持续流入+换手活跃度")
    for rng,lvl,c in [("82-100","强趋/高潮",RED),("68-81","强势主升",(220,110,40)),("52-67","震荡/修复",BLUE),("38-51","弱势观察",G_M),("0-37","退出/回避",GREEN)]:
        pdf.set_fill_color(*c); pdf.rect(LM,pdf.get_y(),8,4.5,"F")
        pdf.set_font("zh","B",6.5); pdf.set_text_color(*c)
        pdf.cell(20,4.5,rng); pdf.set_font("zh","",6.5); pdf.set_text_color(*G_D)
        pdf.cell(30,4.5,lvl); pdf.ln(5.5)
    pdf.ln(3)
    pdf.set_font("zh","",6.5); pdf.set_text_color(*G_D)
    pdf.cell(500,5,"评级: A+(核心主线) / A(强势) / A-(轮动) / B+(支线活跃) / B(支线试探) / C(跟风) / 回避")

    # ═══════════════ P3: 板块评分排名(核心表) + 热力图 ═══════════════
    add_hdr("板块评分排名 — 14日强度透视")
    body("色条越长=评分越高: 红(极强) > 橙(强势) > 蓝(震荡) > 灰(弱势) > 绿(退出)")
    pdf.set_font("zh","B",6); pdf.set_text_color(*NAVY)
    hd = ["板块","评分","5日(亿)","变化","阶段","效应","评级","龙头候选"]
    cw = [100,26,46,26,56,56,26,180]
    x0=LM
    for i,h in enumerate(hd):
        pdf.set_xy(x0+sum(cw[:i]),pdf.get_y()); pdf.cell(cw[i],5.5,h,align="C" if i>0 else "L")
    pdf.ln(6.5)
    y_start = pdf.get_y()
    for idx,s in enumerate(secs[:12]):
        y=y_start+idx*5.8
        col=sc(s["score"])
        # 色条 — 可视化评分
        bar_max=80; bar_w=bar_max*min(s["score"],100)/100
        pdf.set_fill_color(*col)
        pdf.rect(x0-2,y,bar_w,4,style="F")
        pdf.set_draw_color(*G_L); pdf.rect(x0-2,y,bar_max,4,style="D")
        # 文字
        pdf.set_font("zh","",6)
        pdf.set_xy(x0,y); pdf.set_text_color(*G_D); pdf.cell(100,4.5,s['name'][:14])
        pdf.set_xy(x0+100,y); pdf.set_text_color(*sc(s["score"]))
        pdf.cell(26,4.5,f"{s['score']:.0f}",align="C")
        t5=s.get("trend_5d",0); pdf.set_text_color(*G_M)
        pdf.cell(46,4.5,("+"if t5>0 else "")+f"{t5:.0f}亿" if t5!=0 else"持平",align="C")
        dc=s.get("daily_change",0); pdf.set_text_color(*RED if dc>0 else GREEN)
        pdf.cell(26,4.5,("+"if dc>0 else"")+str(dc),align="C")
        pdf.set_text_color(*G_D); pdf.cell(56,4.5,s['stage'],align="C")
        pdf.cell(56,4.5,s['effect'],align="C")
        pdf.set_text_color(*rc(s['rating'])); pdf.cell(26,4.5,s['rating'],align="C")
        pdf.set_text_color(*G_M); pdf.cell(180,4.5," ".join(s.get("leaders",[])[:2]))

    # ═══════════════ P4: 核心板块深度分析 ═══════════════
    add_hdr("核心板块深度分析")
    for s in secs:
        if s["score"]<52: continue
        if pdf.get_y()>135: break
        pdf.set_font("zh","B",7); pdf.set_text_color(*sc(s["score"]))
        pdf.cell(300,5,f"[{s['rating']}] {s['name']} — 评分{s['score']:.0f}"); pdf.ln(5.5)
        c=s['components']
        pdf.set_font("zh","",6.5); pdf.set_text_color(*G_M)
        pdf.cell(400,4,f"涨停散{c['explosive']:.0f}分 | 容量{c['capacity']:.0f}分 | 辨识度{c['recognition']:.0f}分 | 承接{c['absorption']:.0f}分"); pdf.ln(4.5)
        lds=", ".join(s.get("leaders",[])[:3])
        pdf.set_font("zh","",6.5); pdf.set_text_color(*TEAL); pdf.cell(400,4,f"龙头: {lds}"); pdf.ln(5)
        pdf.set_draw_color(*G_L); pdf.line(LM,pdf.get_y(),297-LM,pdf.get_y()); pdf.ln(2)

    # ═══════════════ P5: 龙头选择器 ═══════════════
    add_hdr("龙头选择器")
    pdf.set_font("zh","B",6); pdf.set_text_color(*NAVY)
    for i,h in enumerate(["板块","龙头/核心候选","确定性","明日判断"]):
        pdf.cell(80 if i==0 else(120 if i==1 else(80 if i==2 else 200)),5.5,h,align="L" if i==0 else "C")
    pdf.ln(6)
    for s in secs[:8]:
        lds=", ".join(s.get("leaders",[])[:2])
        cert="高" if s["score"]>=68 else("中" if s["score"]>=52 else"低")
        judge="强修复后观察承接" if s["score"]>=68 else("跟风中需确认" if s["score"]>=52 else"回避/等待")
        pdf.set_font("zh","",6.5)
        pdf.set_text_color(*G_D); pdf.cell(80,5,s['name'][:16])
        pdf.set_text_color(*TEAL); pdf.cell(120,5,lds)
        pdf.set_text_color(*sc(s["score"])); pdf.cell(80,5,cert,align="C")
        pdf.set_text_color(*G_M); pdf.cell(200,5,judge,align="C")
        pdf.ln(5.5)

    # ═══════════════ P6: 强度升降排名 ═══════════════
    add_hdr("强度升降排名 — 资金画出了路线图")
    pdf.set_font("zh","B",8); pdf.set_text_color(*RED)
    pdf.cell(200,6,"上升 TOP5"); pdf.ln(7)
    for g in gainers[:5]:
        pdf.set_font("zh","B",6.5); pdf.set_text_color(*RED)
        pdf.cell(25,5,f"+{g['daily_change']}")
        pdf.set_font("zh","",6.5); pdf.set_text_color(*G_D)
        lds=", ".join(g.get("leaders",[])[:2])
        pdf.cell(300,5,f"{g['name']}  {lds}")
        pdf.ln(5.5)
    pdf.ln(3)
    pdf.set_font("zh","B",8); pdf.set_text_color(*GREEN)
    pdf.cell(200,6,"下降 TOP5"); pdf.ln(7)
    for d in decliners[:5]:
        pdf.set_font("zh","B",6.5); pdf.set_text_color(*GREEN)
        pdf.cell(25,5,f"{d['daily_change']}")
        pdf.set_font("zh","",6.5); pdf.set_text_color(*G_D)
        pdf.cell(300,5,d['name'])
        pdf.ln(5.5)

    # ═══════════════ P7: 实战/观察/回避 ═══════════════
    add_hdr("战略地图 — AI硬件重新成为主战场")
    y0=pdf.get_y()
    for col,(lb,items,c) in enumerate([("实战方向",[s for s in secs if s["structure"]=="主升"],RED),("观察方向",[s for s in secs if s["structure"]=="研究" and s["score"]>=52],BLUE),("回避方向",[s for s in secs if s["structure"]=="杂毛"][:5],GREEN)]):
        x=LM+col*250
        pdf.set_xy(x,y0); pdf.set_font("zh","B",8); pdf.set_text_color(*c)
        pdf.cell(230,5,lb)
        for j,s in enumerate(items[:6]):
            pdf.set_xy(x+5,y0+10+j*7)
            pdf.set_font("zh","",6.5); pdf.set_text_color(*G_D)
            lds=", ".join(s.get("leaders",[])[:2])
            pdf.cell(220,5,f"{s['name'][:12]} {lds}" if lds else s['name'][:12])

    # ═══════════════ P8: 执行清单 ═══════════════
    add_hdr("6月10日执行清单 — 9:40 / 9:45 / 9:50")
    body("时间节点判断: 9:40(龙头续强)→9:45(是否扩散)→9:50(承接到位)→10:30(确认方向)")
    pdf.set_font("zh","B",6); pdf.set_text_color(*NAVY)
    for i,h in enumerate(["时间","看什么","通过条件","失败条件","行动"]):
        pdf.cell(60,5.5,h,align="L" if i==0 else "C")
    pdf.ln(6)
    for t,w,ok,fail,act in [["9:40","龙头是否续强","前排继续强接","核心高开回落","等9:45"],["9:45","是否扩散","半导体/PCB有后排","只有龙头硬顶","只观察"],["9:50","承接是否到位","中军继续上攻","小票涨停/回落","不追涨"],["10:30","确认方向","强线稳住","大面积炸板","加减仓"]]:
        pdf.set_font("zh","B",6.5); pdf.set_text_color(*NAVY); pdf.cell(60,5,t,align="C")
        pdf.set_font("zh","",6); pdf.set_text_color(*G_D); pdf.cell(140,5,w)
        pdf.set_text_color(*TEAL); pdf.cell(180,5,ok)
        pdf.set_text_color(*RED); pdf.cell(180,5,fail)
        pdf.set_font("zh","B",6.5); pdf.set_text_color(*NAVY); pdf.cell(100,5,act,align="C")
        pdf.ln(6)

    # ═══════════════ P9: 重点观察 ═══════════════
    add_hdr("重点观察清单 — 结构确认")
    pdf.set_font("zh","B",6); pdf.set_text_color(*NAVY)
    for i,h in enumerate(["等级","板块","核心观察","触发条件","失败条件"]):
        pdf.cell(50,5.5,h,align="L" if i==0 else "C")
    pdf.ln(6)
    for s in secs[:8]:
        pdf.set_font("zh","B",6.5); pdf.set_text_color(*rc(s['rating']))
        pdf.cell(50,5,s['rating'],align="C")
        pdf.set_font("zh","",6.5); pdf.set_text_color(*G_D); pdf.cell(100,5,s['name'][:14])
        pdf.set_text_color(*G_M); pdf.cell(180,5,", ".join(s.get("leaders",[])[:2]))
        pdf.set_text_color(*TEAL); pdf.cell(180,5,"前排+梯队" if s["score"]>=68 else "观察不参与")
        pdf.set_text_color(*G_L); pdf.cell(100,5,"炸板/高开回落",align="C")
        pdf.ln(5.5)

    # ═══════════════ P10: 市场锚 ═══════════════
    add_hdr("市场锚 — 收盘复盘")
    body(f"沪指+1.28% 深成指+3.02% 创业板+3.93% 成交约26669亿 | 全市场{lu}家涨停 10只连板 封板率84%")
    body(f"最强方向: {secs[0]['name'] if secs else ''}")
    body(f"流出方向: {'/'.join([s['name'] for s in secs if s['score']<38][:3])}")
    pdf.ln(3)
    pdf.set_font("zh","B",8); pdf.set_text_color(*NAVY); pdf.cell(200,6,"复盘三件事"); pdf.ln(7)
    pdf.set_font("zh","",6.5); pdf.set_text_color(*G_D)
    pdf.cell(700,5,f"1. 钱去了哪里? → {secs[0]['name'] if secs else ''}全线强修复"); pdf.ln(5.5)
    pdf.cell(700,5,f"2. 介入深不深? → 评分{secs[0]['score'] if secs else 0:.0f},资金深度介入"); pdf.ln(5.5)
    pdf.cell(700,5,"3. 分歧后回不回来? → 需明日续强确认"); pdf.ln(8)
    pdf.set_font("zh","B",8); pdf.set_text_color(*NAVY)
    pdf.cell(200,6,"核心结论"); pdf.ln(7)
    pdf.set_font("zh","",7); pdf.set_text_color(*G_D)
    pdf.multi_cell(740,4.5,"6月9日的核心不是\"全面上涨\"，而是\"科技硬件从分歧中修复\"。资金没有去新方向。明日只确认强趋势延续，不预判A转B。")

    pdf.output(out)
    print(f"OK: {os.path.getsize(out)/1024:.0f}KB")

if __name__=="__main__":
    dp=os.path.join(BASE,"_analysis_input.json")
    if not os.path.exists(dp):
        print("请先准备数据"); exit(1)
    d=json.load(open(dp,"r",encoding="utf-8"))
    out=os.path.expanduser(r"~/Desktop/智能板块强度仪表盘_2026-06-09_最近14个交易日版.pdf")
    build(d,out)
