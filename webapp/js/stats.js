/**
 * stats.js — Вкладка «Статистика»
 * GET /api/stats?user_id=<id> → Chart.js + аналитика
 */

const QM = {
  '⚡ Бодр':        { emoji:'⚡', color:'#10b981', label:'Бодр'        },
  '😊 Выспался':    { emoji:'😊', color:'#6366f1', label:'Выспался'    },
  '😐 Не выспался': { emoji:'😐', color:'#f59e0b', label:'Не выспался' },
  '💀 Разбит':      { emoji:'💀', color:'#ef4444', label:'Разбит'      },
};
const Q_ORDER = ['⚡ Бодр','😊 Выспался','😐 Не выспался','💀 Разбит'];
const Q_SCORE = { '⚡ Бодр':3,'😊 Выспался':2,'😐 Не выспался':1,'💀 Разбит':0 };

const charts = {};

function applyChartDefaults() {
  if (!window.Chart) return;
  Chart.defaults.color       = '#64748b';
  Chart.defaults.font.family = "'Inter', sans-serif";
  Chart.defaults.font.size   = 12;
}

// ── Точка входа ──────────────────────────────────────────────────────────────
window.initStats = function () {
  applyChartDefaults();

  document.getElementById('view-stats').innerHTML = `
    <div class="page">
      <div class="page-hdr">
        <span class="page-emoji">📊</span>
        <h1>Статистика</h1>
        <p>Твои паттерны сна за последние дни</p>
      </div>
      <div id="stats-body">
        <div class="mini-spin"><div class="spinner"></div><p>Загрузка…</p></div>
      </div>
    </div>`;

  const uid = tg.initDataUnsafe?.user?.id
           || new URLSearchParams(window.location.search).get('user_id');

  if (!uid) { renderError('Не удалось определить пользователя.'); return; }
  fetchStats(uid);
};

// ── Загрузка ─────────────────────────────────────────────────────────────────
async function fetchStats(uid) {
  try {
    const res  = await fetch(`/api/stats?user_id=${uid}`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();

    if (!data.recent?.length) { renderEmpty(); return; }
    render(data);
  } catch (e) {
    console.error(e);
    renderError('Не удалось загрузить данные.<br>Проверь подключение и попробуй позже.');
  }
}

// ── Пустой / ошибка ───────────────────────────────────────────────────────────
function renderEmpty() {
  document.getElementById('stats-body').innerHTML = `
    <div class="empty-box">
      <span class="empty-ico">🌙</span>
      <h2 style="margin-bottom:8px">Пока нет данных</h2>
      <p style="color:var(--hint);font-size:14px">Запиши несколько ночей, чтобы увидеть графики!</p>
      <button class="btn-primary" onclick="goTab('tracker')"
        style="margin-top:20px;max-width:220px">
        <span class="btn-ico">📝</span><span>Записать сон</span>
      </button>
    </div>`;
}

function renderError(msg) {
  document.getElementById('stats-body').innerHTML = `
    <div class="empty-box">
      <span class="empty-ico">⚠️</span>
      <p style="color:var(--hint);font-size:14px">${msg}</p>
    </div>`;
}

// ── Основной рендер ───────────────────────────────────────────────────────────
function render({ week, recent }) {
  document.getElementById('stats-body').innerHTML = `
    <div class="card" id="analytics-card">
      ${buildAnalytics(recent)}
    </div>

    <div class="card">
      <div class="chart-hdr">
        <span class="chart-title">📈 Длительность сна</span>
        <span class="chart-sub">последние ${week.length} ночей</span>
      </div>
      <div class="chart-wrap"><canvas id="bar-chart"></canvas></div>
    </div>

    <div class="card">
      <div class="chart-hdr">
        <span class="chart-title">💭 Качество пробуждений</span>
      </div>
      <div class="donut-wrap"><canvas id="donut-chart"></canvas></div>
    </div>

    <div class="card">
      <div class="chart-hdr">
        <span class="chart-title">📋 История</span>
      </div>
      <div class="log-list">${buildLogs(recent)}</div>
    </div>
  `;

  requestAnimationFrame(() => {
    buildBar(week);
    buildDonut(recent);
  });
}

// ── Аналитическая карточка ────────────────────────────────────────────────────
function buildAnalytics(records) {
  if (records.length < 3) {
    return `<p style="color:var(--hint);font-size:14px;text-align:center">
      Ещё <b style="color:var(--fg)">${3-records.length}</b> запис${records.length===2?'ь':'и'} — и появится персональный анализ!
    </p>`;
  }

  const avg_h = records.reduce((s,r)=>s+r.duration_h,0) / records.length;
  const good  = records.filter(r=>Q_SCORE[r.quality]>=2);
  const ideal_h = good.length ? good.reduce((s,r)=>s+r.duration_h,0)/good.length : avg_h;

  const r7 = records.slice(0,7), p7 = records.slice(7,14);
  const avgR = r7.reduce((s,r)=>s+r.duration_h,0)/r7.length;
  const avgP = p7.length ? p7.reduce((s,r)=>s+r.duration_h,0)/p7.length : avgR;
  const trend = avgR > avgP+.25 ? '📈 растёт' : avgR < avgP-.25 ? '📉 снижается' : '➡️ стабильно';

  return `
    <p class="card-title">✨ Персональная аналитика</p>
    <div class="stat-row">
      <div class="stat-chip"><div class="stat-v">${ideal_h.toFixed(1)}ч</div><div class="stat-l">Идеал</div></div>
      <div class="stat-chip"><div class="stat-v">${avg_h.toFixed(1)}ч</div><div class="stat-l">Среднее</div></div>
      <div class="stat-chip"><div class="stat-v" style="font-size:14px">${trend}</div><div class="stat-l">Тренд</div></div>
    </div>`;
}

// ── Список ────────────────────────────────────────────────────────────────────
function buildLogs(records) {
  return records.slice(0,15).map(r => {
    const m = QM[r.quality] || {emoji:'💤'};
    return `
      <div class="log-row">
        <span class="log-em">${m.emoji}</span>
        <div class="log-inf">
          <div class="log-date">${fmtDate(r.record_date)}</div>
          <div class="log-times">${r.sleep_time} → ${r.wake_time}</div>
        </div>
        <span class="log-dur">${r.duration_h.toFixed(1)}ч</span>
      </div>`;
  }).join('');
}

function fmtDate(s) {
  try { return new Date(s).toLocaleDateString('ru-RU',{day:'numeric',month:'short'}); }
  catch { return s; }
}

// ── Bar chart ─────────────────────────────────────────────────────────────────
function buildBar(records) {
  const ctx = document.getElementById('bar-chart')?.getContext('2d');
  if (!ctx || !window.Chart) return;
  charts.bar?.destroy();

  const idealLine = {
    id:'idealLine',
    afterDraw({ctx:c,chartArea:ca,scales}){
      const y = scales.y.getPixelForValue(7.5);
      if(y<ca.top||y>ca.bottom) return;
      c.save(); c.setLineDash([6,4]);
      c.strokeStyle='rgba(109,40,217,.5)'; c.lineWidth=1.5;
      c.beginPath(); c.moveTo(ca.left,y); c.lineTo(ca.right,y); c.stroke();
      c.restore();
    },
  };

  charts.bar = new Chart(ctx, {
    type: 'bar', plugins: [idealLine],
    data: {
      labels:   records.map(r=>fmtDate(r.record_date)),
      datasets: [{
        label:'Сон (ч)',
        data:         records.map(r=>parseFloat(r.duration_h.toFixed(2))),
        backgroundColor: records.map(r=>(QM[r.quality]?.color??'#6366f1')+'AA'),
        borderColor:     records.map(r=>QM[r.quality]?.color??'#6366f1'),
        borderWidth:1, borderRadius:6, borderSkipped:false,
      }],
    },
    options: {
      responsive:true, maintainAspectRatio:false,
      plugins:{
        legend:{display:false},
        tooltip:{ callbacks:{ label: ctx=>`${ctx.raw}ч · ${records[ctx.dataIndex]?.quality??''}` } },
      },
      scales:{
        x:{ ticks:{maxRotation:45,font:{size:10}}, grid:{color:'rgba(255,255,255,.04)'}, border:{display:false} },
        y:{ min:0,max:12, ticks:{callback:v=>`${v}ч`,stepSize:3}, grid:{color:'rgba(255,255,255,.05)'}, border:{display:false} },
      },
    },
  });
}

// ── Doughnut chart ────────────────────────────────────────────────────────────
function buildDonut(records) {
  const ctx = document.getElementById('donut-chart')?.getContext('2d');
  if (!ctx || !window.Chart) return;
  charts.donut?.destroy();

  const counts = Object.fromEntries(Q_ORDER.map(k=>[k,0]));
  records.forEach(r=>{ if(counts[r.quality]!==undefined) counts[r.quality]++; });

  charts.donut = new Chart(ctx, {
    type:'doughnut',
    data:{
      labels:   Q_ORDER.map(k=>`${QM[k].emoji} ${QM[k].label}`),
      datasets:[{
        data:            Q_ORDER.map(k=>counts[k]),
        backgroundColor: Q_ORDER.map(k=>QM[k].color+'CC'),
        borderColor:     Q_ORDER.map(k=>QM[k].color),
        borderWidth:2, hoverOffset:10,
      }],
    },
    options:{
      responsive:true, maintainAspectRatio:true, cutout:'66%',
      plugins:{
        legend:{
          display:true, position:'bottom',
          labels:{padding:16,usePointStyle:true,pointStyleWidth:10,font:{size:12}},
        },
        tooltip:{ callbacks:{ label:ctx=>` ${ctx.raw} раз` } },
      },
    },
  });
}
