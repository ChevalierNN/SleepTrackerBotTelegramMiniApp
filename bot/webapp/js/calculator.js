/**
 * calculator.js — Вкладка «Калькулятор» циклов сна
 *
 * Два режима:
 *  1. «Лечь сейчас»  → показывает 4 варианта пробуждения
 *  2. «Проснуться в» → вводишь время будильника → показывает когда лечь
 *
 * Вся логика — клиентская, не требует сервера.
 */

const CYCLE_MIN  = 90;   // минут в одном цикле
const FALL_MIN   = 15;   // среднее время засыпания
const CYCLES_ALL = [3, 4, 5, 6];

const pad2 = n => String(n).padStart(2, '0');

function addMinutes(date, m) {
  return new Date(date.getTime() + m * 60000);
}

function fmtTime(date) {
  return `${pad2(date.getHours())}:${pad2(date.getMinutes())}`;
}

function fmtDur(min) {
  const h = Math.floor(min / 60), m = min % 60;
  return m ? `${h}ч ${m}мин` : `${h}ч`;
}

function cycleClass(n) {
  if (n >= 5) return 'best';
  if (n >= 4) return 'good';
  return 'ok';
}

function cycleBadge(n) {
  if (n >= 5) return `<span class="c-badge badge-green">✅ ${n} цикл${n===5?'ов':'ов'}</span>`;
  if (n >= 4) return `<span class="c-badge badge-blue">👍 ${n} цикла</span>`;
  return       `<span class="c-badge badge-gray">😐 ${n} цикла</span>`;
}

function cycleEmoji(n) {
  if (n >= 5) return '🌟';
  if (n >= 4) return '😊';
  return '😐';
}

// ── Рендер результатов «лечь сейчас» ────────────────────────────────────────
function renderSleepNow() {
  const now = new Date();
  const fallAt = addMinutes(now, FALL_MIN);

  const cards = CYCLES_ALL.map(n => {
    const wakeAt = addMinutes(fallAt, n * CYCLE_MIN);
    const dur    = n * CYCLE_MIN;
    const cls    = cycleClass(n);
    return `
      <div class="cycle-card ${cls}">
        <span class="c-ico">${cycleEmoji(n)}</span>
        <div class="c-info">
          <div class="c-time">${fmtTime(wakeAt)}</div>
          <div class="c-meta">Сон ${fmtDur(dur)} · засни в ${fmtTime(fallAt)}</div>
        </div>
        ${cycleBadge(n)}
      </div>
    `;
  }).join('');

  return `
    <p class="card-title">⏰ Оптимальное пробуждение</p>
    <div class="cycles-grid">${cards}</div>
  `;
}

// ── Рендер результатов «под будильник» ──────────────────────────────────────
function renderAlarm(alarmVal) {
  if (!alarmVal) return `<p style="color:var(--hint);text-align:center;margin-top:8px">Введи время будильника ↑</p>`;

  const [h, m] = alarmVal.split(':').map(Number);
  const now = new Date();
  let alarm = new Date(now.getFullYear(), now.getMonth(), now.getDate(), h, m);
  if (alarm <= now) alarm.setDate(alarm.getDate() + 1);

  const cards = [...CYCLES_ALL].reverse().map(n => {
    const sleepAt = addMinutes(alarm, -(n * CYCLE_MIN + FALL_MIN));
    const dur     = n * CYCLE_MIN;
    const cls     = cycleClass(n);
    return `
      <div class="cycle-card ${cls}">
        <span class="c-ico">${cycleEmoji(n)}</span>
        <div class="c-info">
          <div class="c-time">${fmtTime(sleepAt)}</div>
          <div class="c-meta">Ляг в это время · сон ${fmtDur(dur)}</div>
        </div>
        ${cycleBadge(n)}
      </div>
    `;
  }).join('');

  return `
    <p class="card-title">🛏 Когда лечь спать</p>
    <div class="cycles-grid">${cards}</div>
  `;
}

// ── Сборка HTML ─────────────────────────────────────────────────────────────
function buildCalcHTML() {
  return `
    <div class="page">
      <div class="page-hdr">
        <span class="page-emoji">⏰</span>
        <h1>Калькулятор сна</h1>
        <p>90-минутные циклы для идеального пробуждения</p>
      </div>

      <div class="mode-switch">
        <button class="mode-btn active" id="mode-now">😴 Лечь сейчас</button>
        <button class="mode-btn"       id="mode-alarm">⏰ Под будильник</button>
      </div>

      <!-- Блок «лечь сейчас» -->
      <div class="card" id="block-now">
        <div id="results-now">${renderSleepNow()}</div>
        <div class="hint" style="margin-top:12px">
          <span class="hint-ico">💡</span>
          <span>5–6 циклов (7.5–9 часов) — оптимально. Зелёные варианты — лучший выбор.</span>
        </div>
      </div>

      <!-- Блок «под будильник» -->
      <div class="card hidden" id="block-alarm">
        <div class="time-field">
          <label class="field-lbl" for="alarm-inp">⏰ Время пробуждения</label>
          <input type="time" id="alarm-inp" class="time-inp" value="">
        </div>
        <div id="results-alarm" style="margin-top:14px">${renderAlarm('')}</div>
        <div class="hint" style="margin-top:12px">
          <span class="hint-ico">💡</span>
          <span>Начинай считать <b>от будильника назад</b> — так выбираешь точное время для сна.</span>
        </div>
      </div>
    </div>
  `;
}

// ── Инициализация ────────────────────────────────────────────────────────────
window.initCalculator = function () {
  const view = document.getElementById('view-calculator');
  view.innerHTML = buildCalcHTML();

  const modeNow   = document.getElementById('mode-now');
  const modeAlarm = document.getElementById('mode-alarm');
  const blockNow  = document.getElementById('block-now');
  const blockAlarm= document.getElementById('block-alarm');
  const alarmInp  = document.getElementById('alarm-inp');
  const resAlarm  = document.getElementById('results-alarm');

  modeNow.addEventListener('click', () => {
    modeNow.classList.add('active'); modeAlarm.classList.remove('active');
    blockNow.classList.remove('hidden'); blockAlarm.classList.add('hidden');
    // Обновляем «сейчас» при каждом переключении
    document.getElementById('results-now').innerHTML = renderSleepNow();
    if (tg.HapticFeedback) tg.HapticFeedback.selectionChanged();
  });

  modeAlarm.addEventListener('click', () => {
    modeAlarm.classList.add('active'); modeNow.classList.remove('active');
    blockAlarm.classList.remove('hidden'); blockNow.classList.add('hidden');
    if (tg.HapticFeedback) tg.HapticFeedback.selectionChanged();
  });

  alarmInp.addEventListener('change', () => {
    resAlarm.innerHTML = renderAlarm(alarmInp.value);
  });
};
