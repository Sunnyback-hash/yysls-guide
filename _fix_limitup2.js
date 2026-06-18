const fs = require('fs');
let h = fs.readFileSync(__dirname + '/market.html', 'utf8');

// Use flexible approach - find the content by context
// The table rows start with flow-badge markers

// Find and replace the 4连板 row
const old4 = 'flow-badge in" style="font-size:13px;padding:4px 12px">4连板</span></td><td style="font-weight:600;color:var(--rise)">3只</td><td class="stock-name">华电能源 华塑控股 香江控股</td><td>电力/PCB/地产</td></tr>';
const new4 = 'flow-badge in" style="font-size:13px;padding:4px 12px">5连板</span></td><td style="font-weight:600;color:var(--rise)">2只</td><td class="stock-name">华电能源 香江控股</td><td>电力/地产 🏆</td></tr>';

if (h.includes(old4)) {
  h = h.replace(old4, new4);
  console.log('Fixed 4→5连板');
} else {
  console.log('NOT FOUND: 4连板 row');
}

// 3连板 row
const old3 = 'class="flow-badge out" style="font-size:13px;padding:4px 12px">3连板</span></td><td style="font-weight:600">1只</td><td class="stock-name">中京电子</td><td>PCB</td></tr>';
const new3 = 'class="flow-badge out" style="font-size:13px;padding:4px 12px">3连板</span></td><td style="font-weight:600">2只</td><td class="stock-name">粤电力A 合锻智能</td><td>电力/设备</td></tr>';

if (h.includes(old3)) {
  h = h.replace(old3, new3);
  console.log('Fixed 3连板');
}

// 2连板 row
const old2 = 'class="stock-name">粤电力A 江海股份 德新科技 合锻智能 艾华集团</td>';
const new2 = 'class="stock-name">华锋股份 江海股份 博杰股份 天地在线</td>';

if (h.includes(old2)) {
  h = h.replace(old2, new2);
  console.log('Fixed 2连板');
}

// 首板 row
const old1 = 'font-weight:600;color:var(--gold)">92只</td><td>批量爆发</td><td>电力/电子/通信</td></tr>';
const new1 = 'font-weight:600;color:var(--gold)">39只</td><td>消费/电力/地产</td><td>板块轮动</td></tr>';

if (h.includes(old1)) {
  h = h.replace(old1, new1);
  console.log('Fixed 首板');
}

// Update analysis text
const oldAnalysis = '3进4：<strong style="color:var(--rise)">全部晋级（100%）</strong> — 情绪修复的明确信号<br>\n\t        2进3：中京电子晋级，其他竞争失败 — 科技线强度确认<br>\n\t        首板爆发92只 — 资金全面进场，梯队完整';
const newAnalysis = '4进5：<strong style="color:var(--rise)">华电+香江晋级（66%）</strong> — 华塑天地板分歧<br>\n\t        华塑控股：<strong style="color:var(--fall)">天地板</strong> 澄清未从事PCB业务<br>\n\t        首板仅39只 — 科技退潮压制情绪';

if (h.includes(oldAnalysis)) {
  h = h.replace(oldAnalysis, newAnalysis);
  console.log('Fixed analysis text');
}

// Update trend stocks
const trendOld = '宝鼎科技\",perf:\"16天10板\",dir:\"PCB趋势龙\",strat:\"5日线低吸\"';
const trendNew = '亨通光电\",perf:\"涨停+40亿\",dir:\"光纤龙一\",strat:\"分歧低吸\"';

if (h.includes(trendOld)) {
  h = h.replace(trendOld, trendNew);
  console.log('Fixed trend: 宝鼎→亨通');
}

const oldTrend2 = '风华高科\",perf:\"8天4板\",dir:\"MLCC龙头\",strat:\"断板低吸\"';
const newTrend2 = '香江控股\",perf:\"5连板\",dir:\"地产龙头\",strat:\"打回封\"';

if (h.includes(oldTrend2)) {
  h = h.replace(oldTrend2, newTrend2);
  console.log('Fixed trend: 风华→香江');
}

const oldTrend3 = '艾华集团\",perf:\"9天5板\",dir:\"超级电容\",strat:\"趋势持有\"';
const newTrend3 = '步步高\",perf:\"4天3板\",dir:\"零售龙头\",strat:\"分歧低吸\"';

if (h.includes(oldTrend3)) {
  h = h.replace(oldTrend3, newTrend3);
  console.log('Fixed trend: 艾华→步步高');
}

const oldTrend4 = '黄河旋风\",perf:\"5天4板\",dir:\"金刚石散热\",strat:\"分歧低吸\"';
const newTrend4 = '粤电力A\",perf:\"3连板\",dir:\"电力龙二\",strat:\"板块联动\"';

if (h.includes(oldTrend4)) {
  h = h.replace(oldTrend4, newTrend4);
  console.log('Fixed trend: 黄河→粤电力A');
}

const oldTrend5 = '中兴通讯\",perf:\"涨停+22亿\",dir:\"通信中军\",strat:\"大资金做T\"';
const newTrend5 = '华电能源\",perf:\"5连板\",dir:\"电力总龙\",strat:\"板上确认\"';

if (h.includes(oldTrend5)) {
  h = h.replace(oldTrend5, newTrend5);
  console.log('Fixed trend: 中兴→华电能源');
}

// Update sentiment push text
const oldSent = '⬤ 当前 修复期：涨停127只，最高标4板，封板率83%<br>\n\t        ➤ 若华电能源/华塑控股升级5板 → ';
const newSent = '⬤ 当前 分化调整期：涨停70只，跌停106只，最高标5板，封板率56%<br>\n\t        ➤ 华电/香江5板穿越→华塑天地板分歧';

if (h.includes(oldSent)) {
  h = h.replace(oldSent, newSent);
  console.log('Fixed sentiment phase text');
}

const oldSent2 = '若断板且无接力 → <strong style="color:var(--fall)">可能二次退潮</strong>，注意风险';
const newSent2 = '科技退潮vs消费地产承接 → <strong style="color:var(--gold)">结构市重板块轻指数</strong>';

if (h.includes(oldSent2)) {
  h = h.replace(oldSent2, newSent2);
  console.log('Fixed sentiment conclusion');
}

// Update the stockPicks reason text that mentions 28日 data
h = h.replace('周一若6板成功则确认电力主升', '周二预期6板PK 市场总龙头争夺');
h = h.replace('周一6板PK，胜者成为市场总龙头', '周二5进6PK 胜者晋级败者断板');

fs.writeFileSync(__dirname + '/market.html', h);
console.log('Done. Size:', h.length);

// Validate
const jsStart = h.lastIndexOf('<script>');
const jsEnd = h.lastIndexOf('</script>');
const js = h.substring(jsStart + 8, jsEnd);
try {
  new Function(js);
  console.log('Syntax: OK');
} catch(e) {
  console.log('Syntax ERROR:', e.message);
}
