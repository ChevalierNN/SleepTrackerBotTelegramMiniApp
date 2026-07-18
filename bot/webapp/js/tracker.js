/**
 * tracker.js — Вкладка «Запись сна»
 *
 * Сохраняет данные через POST /api/sleep (прямой API).
 * Fallback: Telegram.WebApp.sendData() если сервер недоступен.
 */

const QUALITY_OPTS = [
  { key: 'great', emoji: '⚡', label: 'Бодр',       dbVal: '⚡ Бодр'        },
  { key: 'good',  emoji: '😊', label: 'Выспался',    dbVal: '😊 Выспался'    },
  { key: 'poor',  emoji: '😐', label: 'Не выспался', dbVal: '😐 Не выспался' },
  { key: 'awful', emoji: '💀', label: 'Разбит',      dbVal: '💀 Разбит'      },
];

const CYCLE_M = 90;
const pad = n => String(n).padStart(2, '0');
const toMin = v => { const [h,m] = v.split(':').map(Number); return h*60+m; };

function fmtDur(min) {
  const h = Math.floor(min/60), m = min%60;
  return m ? `${h}ч ${m}мин` : `${h}ч`;
}

function hintFor(dur) {
  const cyc = dur / CYCLE_M;
  const dev = Math.abs(cyc - Math.round(cyc));
  if (dur < 270) return { cls: 'h-warn', ico: '⚠️', txt: 'Меньше 4.5 ч — слишком мало для восстановления.' };
  if (dev < 0.17 && cyc >= 3) return { cls: 'h-ok', ico: '✅', txt: `Отлично! Ты просыпаешься после ${Math.round(cyc)} полных 90-мин циклов.` };
  return { cls: '', ico: '💡', txt: 'Идеально просыпаться через 4.5, 6 или 7.5 ч — в конце цикла.' };
}

// ── Сборка HTML ──────────────────────────────────────────────────────────────
function buildTrackerHTML(defSleep, defWake) {
  const qBtns = QUALITY_OPTS.map(q => `
    <button class="q-btn" data-q="${q.key}">
      <span class="q-emoji">${q.emoji}</span>
      <span class="q-lbl">${q.label}</span>
    </button>`).join('');

  return `
    <div class="page">
      <div class="page-hdr">
        <span class="page-emoji">🌙</span>
        <h1>Запись сна</h1>
        <p>Зафиксируй прошедшую ночь</p>
      </div>

      <div class="card">
        <p class="card-title">🕐 Время сна</p>
        <div style="display:flex;gap:12px;align-items:flex-end">
          <div class="time-field" style="flex:1">
            <label class="field-lbl" for="sl-inp">🛏 Засыпание</label>
            <input type="time" id="sl-inp" class="time-inp" value="${defSleep}">
          </div>
          <div style="padding:0 4px 14px;color:var(--hint);font-size:18px;">→</div>
          <div class="time-field" style="flex:1">
            <label class="field-lbl" for="wk-inp">☀️ Пробуждение</label>
            <input type="time" id="wk-inp" class="time-inp" value="${defWake}">
          </div>
        </div>

        <div class="dur-bar">
          <span>⏱</span>
          <span id="dur-val">—</span>
        </div>
      </div>

      <div class="card">
        <p class="card-title">💬 Самочувствие</p>
        <div class="q-grid">${qBtns}</div>
      </div>

      <div class="hint" id="sleep-hint">
        <span class="hint-ico">💡</span>
        <span id="hint-text">Идеально просыпаться через 4.5, 6 или 7.5 ч — в конце 90-мин цикла.</span>
      </div>

      <button class="btn-primary" id="save-btn" disabled style="margin-top:4px">
        <span class="btn-ico">✨</span>
        <span id="save-lbl">Выбери самочувствие</span>
      </button>
    </div>
  `;
}

// ── Инициализация ────────────────────────────────────────────────────────────
window.initTracker = function () {
  const view = document.getElementById('view-tracker');

  const now   = new Date();
  const wakeD = new Date(now.getTime() + 7.5 * 3600 * 1000);
  const defSl = `${pad(now.getHours())}:${pad(now.getMinutes())}`;
  const defWk = `${pad(wakeD.getHours())}:${pad(wakeD.getMinutes())}`;

  view.innerHTML = buildTrackerHTML(defSl, defWk);
  attachLogic();
};

// ── Логика формы ─────────────────────────────────────────────────────────────
function attachLogic() {
  let selQ = null;

  const slInp  = document.getElementById('sl-inp');
  const wkInp  = document.getElementById('wk-inp');
  const durVal = document.getElementById('dur-val');
  const hint   = document.getElementById('sleep-hint');
  const hintT  = document.getElementById('hint-text');
  const saveBtn= document.getElementById('save-btn');
  const saveLbl= document.getElementById('save-lbl');

  function update() {
    if (!slInp.value || !wkInp.value) return;
    let sl = toMin(slInp.value), wk = toMin(wkInp.value);
    if (wk <= sl) wk += 24 * 60;
    const dur = wk - sl;
    durVal.textContent = fmtDur(dur);

    const h = hintFor(dur);
    hint.className = `hint ${h.cls}`;
    hintT.innerHTML = `${h.ico} ${h.txt}`;
  }

  slInp.addEventListener('change', update);
  wkInp.addEventListener('change', update);
  update();

  // Кнопки качества
  document.querySelectorAll('.q-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.q-btn').forEach(b => b.classList.remove('sel'));
      btn.classList.add('sel');
      selQ = QUALITY_OPTS.find(q => q.key === btn.dataset.q);

      saveBtn.disabled = false;
      saveBtn.classList.add('ready');
      saveLbl.textContent = 'Сохранить запись';
      if (tg.HapticFeedback) tg.HapticFeedback.selectionChanged();
    });
  });

  // Сохранение
  saveBtn.addEventListener('click', async () => {
    if (!selQ) return;

    let sl = toMin(slInp.value), wk = toMin(wkInp.value);
    if (wk <= sl) wk += 24 * 60;
    const duration_h = parseFloat(((wk - sl) / 60).toFixed(2));

    const userId = tg.initDataUnsafe?.user?.id;

    saveBtn.disabled = true;
    saveLbl.textContent = 'Сохранение...';

    if (userId) {
      // Основной путь: POST /api/sleep
      try {
        const resp = await fetch('/api/sleep', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            user_id:    userId,
            sleep_time: slInp.value,
            wake_time:  wkInp.value,
            duration_h,
            quality:    selQ.dbVal,
          }),
        });
        const data = await resp.json();
        if (!data.ok) throw new Error(data.error || 'server error');

        showToast('✅ Запись сохранена!');
        if (tg.HapticFeedback) tg.HapticFeedback.notificationOccurred('success');

        // Сброс формы
        document.querySelectorAll('.q-btn').forEach(b => b.classList.remove('sel'));
        selQ = null;
        saveBtn.disabled  = true;
        saveBtn.classList.remove('ready');
        saveLbl.textContent = 'Выбери самочувствие';
      } catch (e) {
        showToast('❌ Ошибка: ' + e.message, true);
        saveBtn.disabled = false;
        saveLbl.textContent = 'Сохранить запись';
        if (tg.HapticFeedback) tg.HapticFeedback.notificationOccurred('error');
      }
    } else {
      // Fallback: sendData() → бот получает через web_app_data
      const payload = JSON.stringify({
        action: 'save_sleep',
        sleep_time: slInp.value,
        wake_time:  wkInp.value,
        duration_h,
        quality: selQ.dbVal,
      });
      tg.sendData(payload);
      if (tg.HapticFeedback) tg.HapticFeedback.notificationOccurred('success');
      setTimeout(() => tg.close(), 800);
    }
  });
}
