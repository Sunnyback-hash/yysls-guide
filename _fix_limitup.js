const fs = require('fs');
let h = fs.readFileSync(__dirname + '/market.html', 'utf8');

// Fix 1: Hardcoded limitUp table (lines ~1490-1501)
const oldLimitTable = `<tr><td><span class="flow-badge in" style="font-size:13px;padding:4px 12px">4连板</span></td><td style="font-weight:600;color:var(--rise)">3只</td><td class="stock-name">华电能源 华塑控股 香江控股</td><td>电力/PCB/地产</td></tr>
\t          <tr><td><span class="flow-badge out" style="font-size:13px;padding:4px 12px">3连板</span></td><td style="font-weight:600">1只</td><td class="stock-name">中京电子</td><td>PCB</td></tr>
\t          <tr><td><span style="font-size:13px;padding:4px 12px">2连板</span></td><td>5只</td><td class="stock-name">粤电力A 江海股份 德新科技 合锻智能 艾华集团</td><td>电力/电容/机器人</td></tr>
\t          <tr><td><span style="font-size:13px;padding:4px 12px">首板</span></td><td style="font-weight:600;color:var(--gold)">92只</td><td>批量爆发</td><td>电力/电子/通信</td></tr>
\t        </tbody></table>
\t      </div>
\t      <div style="margin-top:12px;font-size:12px;color:var(--text2);line-height:1.8">
\t        <strong style="color:var(--text)">晋级率分析：</strong><br>
\t        3进4：<strong style="color:var(--rise)">全部晋级（100%）</strong> — 情绪修复的明确信号<br>
\t        2进3：中京电子晋级，其他竞争失败 — 科技线强度确认<br>
\t        首板爆发92只 — 资金全面进场，梯队完整`;

const newLimitTable = `<tr><td><span class="flow-badge in" style="font-size:13px;padding:4px 12px">5连板</span></td><td style="font-weight:600;color:var(--rise)">2只</td><td class="stock-name">华电能源 香江控股</td><td>电力/地产</td></tr>
\t          <tr><td><span class="flow-badge out" style="font-size:13px;padding:4px 12px">3连板</span></td><td style="font-weight:600">2只</td><td class="stock-name">粤电力A 合锻智能</td><td>电力/设备</td></tr>
\t          <tr><td><span style="font-size:13px;padding:4px 12px">2连板</span></td><td>5只</td><td class="stock-name">华锋股份 江海股份 博杰股份 天地在线</td><td>汽车/电容/机器人</td></tr>
\t          <tr><td><span style="font-size:13px;padding:4px 12px">首板</span></td><td style="font-weight:600;color:var(--gold)">39只</td><td>消费/电力/地产</td><td>轮动</td></tr>
\t        </tbody></table>
\t      </div>
\t      <div style="margin-top:12px;font-size:12px;color:var(--text2);line-height:1.8">
\t        <strong style="color:var(--text)">晋级率分析：</strong><br>
\t        4进5：<strong style="color:var(--rise)">华电+香江晋级（66%）</strong> — 华塑天地板警示风险<br>
\t        华塑控股：<strong style="color:var(--fall)">天地板</strong> — 公司澄清未从事PCB业务<br>
\t        首板仅39只（-53只）— 科技退潮压制情绪`;

if (h.includes(oldLimitTable)) {
  h = h.replace(oldLimitTable, newLimitTable);
  console.log('Fixed limitUp table');
} else {
  console.log('WARN: limitUp table pattern not found');
}

// Fix 2: Trend stock table
const oldTrend = `{name:'宝鼎科技',perf:'16天10板',dir:'PCB趋势龙',strat:'5日线低吸'},
\t            {name:'风华高科',perf:'8天4板',dir:'MLCC龙头',strat:'断板低吸'},
\t            {name:'艾华集团',perf:'9天5板',dir:'超级电容',strat:'趋势持有'},
\t            {name:'黄河旋风',perf:'5天4板',dir:'金刚石散热',strat:'分歧低吸'},
\t            {name:'中兴通讯',perf:'涨停+22亿',dir:'通信中军',strat:'大资金做T'}`;

const newTrend = `{name:'亨通光电',perf:'涨停+40亿',dir:'光纤龙一',strat:'分歧低吸'},
\t            {name:'香江控股',perf:'5连板',dir:'地产龙头',strat:'打回封'},
\t            {name:'步步高',perf:'4天3板',dir:'零售龙头',strat:'分歧低吸'},
\t            {name:'粤电力A',perf:'3连板',dir:'电力龙二',strat:'板块联动'},
\t            {name:'华电能源',perf:'5连板',dir:'电力总龙',strat:'板上确认'}`;

if (h.includes(oldTrend)) {
  h = h.replace(oldTrend, newTrend);
  console.log('Fixed trend table');
} else {
  console.log('WARN: trend table pattern not found');
}

// Fix 3: Sentiment cycle push
const oldPush = `⬤ 当前 修复期：涨停127只，最高标4板，封板率83%<br>
\t        ➤ 若华电能源/华塑控股升级5板 → <strong style="color:var(--gold)">确认进入主升期</strong><br>
\t        ➤ 若断板且无接力 → <strong style="color:var(--fall)">可能二次退潮</strong>，注意风险`;

const newPush = `⬤ 当前 分化调整期：涨停70只，跌停106只，最高标5板，封板率56%<br>
\t        ➤ 华电/香江5板穿越成功 — 但华塑天地板 + 科技跌停潮<br>
\t        ➤ 科技退潮 vs 消费地产承接 → <strong style="color:var(--gold)">结构市，重板块轻指数</strong>`;

if (h.includes(oldPush)) {
  h = h.replace(oldPush, newPush);
  console.log('Fixed sentiment push');
} else {
  console.log('WARN: sentiment push not found');
}

// Fix 4: Update checklist items
if (h.includes('华电能源能否5连板')) {
  h = h.replace(
    '华电能源能否5连板（情绪突破信号）',
    '科技股(半导体/光模块)是否止跌企稳'
  );
  h = h.replace(
    '华塑控股/中京电子晋级情况（科技线强度）',
    '电力板块(华电/粤电力)分歧承接力度'
  );
  h = h.replace(
    '两市成交额是否重回3万亿+',
    '消费/地产板块持续性验证'
  );
  h = h.replace(
    '电力板块分歧承接（华电断板时有无补涨）',
    '北向资金能否持续流入权重股'
  );
  h = h.replace(
    '创业板指/科创50是否继续领涨',
    '半导体是否出现止跌信号(华天/京东方)'
  );
  console.log('Fixed checklist');
}

fs.writeFileSync(__dirname + '/market.html', h);
console.log('Done. Size:', h.length);

// Verify syntax
const jsStart = h.lastIndexOf('<script>');
const jsEnd = h.lastIndexOf('</script>');
const js = h.substring(jsStart + 8, jsEnd);
try {
  new Function(js);
  console.log('Syntax: OK');
} catch(e) {
  console.log('Syntax ERROR:', e.message);
}
