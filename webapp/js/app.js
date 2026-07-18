/**
 * app.js — Telegram Mini App инициализация + таб-роутер
 */

const tg = window.Telegram.WebApp;
tg.ready();
tg.expand();

// ── Таб-роутер ────────────────────────────────────────────────
const TABS = ['calculator', 'tracker', 'stats'];

const INITS = {
  calculator: () => typeof initCalculator === 'function' && initCalculator(),
  tracker:    () => typeof initTracker    === 'function' && initTracker(),
  stats:      () => typeof initStats      === 'function' && initStats(),
};

let activeTab = null;
const initialized = new Set();

function switchTab(name) {
  if (!TABS.includes(name) || name === activeTab) return;
  activeTab = name;

  // Переключаем вкладки
  TABS.forEach(t => {
    document.getElementById(`view-${t}`)?.classList.toggle('active', t === name);
    document.getElementById(`tab-${t}`)?.classList.toggle('active', t === name);
  });

  // Инициализируем только один раз
  if (!initialized.has(name)) {
    initialized.add(name);
    INITS[name]?.();
  }

  if (tg.HapticFeedback) tg.HapticFeedback.selectionChanged();
}

// Публичная функция для переключения из других модулей
window.goTab = switchTab;

// ── Toast уведомления ─────────────────────────────────────────
let toastTimer = null;
window.showToast = function (msg, isError = false) {
  let el = document.getElementById('global-toast');
  if (!el) {
    el = document.createElement('div');
    el.id = 'global-toast';
    el.className = 'toast';
    document.body.appendChild(el);
  }
  el.textContent = msg;
  el.className = `toast${isError ? ' error' : ''}`;
  requestAnimationFrame(() => el.classList.add('show'));
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => el.classList.remove('show'), 2500);
};

// ── Навесить обработчики на таббар ────────────────────────────
document.querySelectorAll('.tab-btn').forEach(btn => {
  btn.addEventListener('click', () => switchTab(btn.dataset.tab));
});

// ── Определить стартовую вкладку ──────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  const hash = window.location.hash.replace('#', '');
  const start = TABS.includes(hash) ? hash : 'calculator';
  switchTab(start);
});
