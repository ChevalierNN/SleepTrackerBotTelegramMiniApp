"""
Statistics handler: generates a weekly sleep chart and sends it as a photo.
"""

import io
from datetime import datetime, timedelta, date

import matplotlib
matplotlib.use("Agg")  # non-interactive backend (no GUI)
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.ticker import MultipleLocator

from aiogram import Router, F
from aiogram.types import CallbackQuery, BufferedInputFile

from database import get_week_records
from keyboards import back_to_main

router = Router(name="stats")

# Цвета для каждой оценки качества
QUALITY_COLORS = {
    "⚡ Бодр":        "#4ade80",   # зелёный
    "😊 Выспался":    "#60a5fa",   # синий
    "😐 Не выспался": "#fbbf24",   # жёлтый
    "💀 Разбит":      "#f87171",   # красный
}
DEFAULT_COLOR = "#94a3b8"  # серый для неизвестных значений

QUALITY_ORDER = ["⚡ Бодр", "😊 Выспался", "😐 Не выспался", "💀 Разбит"]


def _build_chart(records: list[dict], username: str) -> bytes:
    """Строит график сна и возвращает PNG-байты."""

    # Создаём диапазон дат за 7 дней
    today = date.today()
    days = [today - timedelta(days=i) for i in reversed(range(7))]
    day_labels = [d.strftime("%d.%m\n%a") for d in days]

    # Переводим записи в словарь по дате
    records_by_date: dict[str, dict] = {r["record_date"]: r for r in records}

    durations = []
    colors = []
    has_data = []

    for d in days:
        key = d.isoformat()
        if key in records_by_date:
            rec = records_by_date[key]
            durations.append(rec["duration_h"])
            colors.append(QUALITY_COLORS.get(rec["quality"], DEFAULT_COLOR))
            has_data.append(True)
        else:
            durations.append(0)
            colors.append("#1e293b")
            has_data.append(False)

    # ── Рисуем график ──────────────────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(10, 5.5))
    fig.patch.set_facecolor("#0f172a")
    ax.set_facecolor("#0f172a")

    x = range(len(days))
    bars = ax.bar(x, durations, color=colors, width=0.6, zorder=3, edgecolor="#1e293b", linewidth=1.2)

    # Линия оптимального сна
    ax.axhline(y=7.5, color="#818cf8", linewidth=1.5, linestyle="--", alpha=0.7, zorder=2)
    ax.axhline(y=9.0, color="#818cf8", linewidth=1.5, linestyle="--", alpha=0.4, zorder=2)
    ax.text(6.55, 7.55, "7.5ч", color="#818cf8", fontsize=8, va="bottom")
    ax.text(6.55, 9.05, "9ч",   color="#818cf8", fontsize=8, va="bottom")

    # Подписи значений над столбцами
    for i, (bar, dur, has) in enumerate(zip(bars, durations, has_data)):
        if has:
            h = bar.get_height()
            hrs = int(dur)
            mins = int((dur - hrs) * 60)
            label = f"{hrs}ч {mins}м" if mins else f"{hrs}ч"
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                h + 0.1,
                label,
                ha="center", va="bottom",
                color="white", fontsize=9, fontweight="bold",
            )
        else:
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                0.15,
                "нет\nданных",
                ha="center", va="bottom",
                color="#475569", fontsize=7.5,
            )

    # Сетка и оси
    ax.set_xticks(list(x))
    ax.set_xticklabels(day_labels, color="#94a3b8", fontsize=9)
    ax.set_ylabel("Часов сна", color="#94a3b8", fontsize=10)
    ax.set_ylim(0, max(max(durations) + 1.5, 11))
    ax.yaxis.set_minor_locator(MultipleLocator(0.5))
    ax.tick_params(axis="y", colors="#94a3b8", labelsize=9)
    ax.tick_params(axis="x", which="both", bottom=False)
    ax.spines[["top", "right", "left", "bottom"]].set_visible(False)
    ax.grid(axis="y", color="#1e293b", linewidth=1, zorder=0)

    # Заголовок
    ax.set_title(
        f"📊 Статистика сна за 7 дней  ·  {username}",
        color="white", fontsize=13, fontweight="bold", pad=14,
    )

    # Легенда
    patches = [
        mpatches.Patch(color=QUALITY_COLORS[q], label=q)
        for q in QUALITY_ORDER
    ]
    patches.append(mpatches.Patch(color=DEFAULT_COLOR, label="Нет данных"))
    legend = ax.legend(
        handles=patches,
        loc="upper left",
        frameon=True,
        facecolor="#1e293b",
        edgecolor="#334155",
        labelcolor="white",
        fontsize=8.5,
        handlelength=1.2,
    )

    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=150, facecolor=fig.get_facecolor())
    plt.close(fig)
    buf.seek(0)
    return buf.read()


@router.callback_query(F.data == "menu_stats")
async def show_stats(callback: CallbackQuery) -> None:
    await callback.answer("Генерирую график…")

    records = await get_week_records(callback.from_user.id)

    if not records:
        await callback.message.edit_text(
            "📊 <b>Статистика за 7 дней</b>\n\n"
            "😕 Записей о сне пока нет.\n\n"
            "Используй кнопку <b>«Записать сон»</b>, чтобы начать вести дневник!",
            parse_mode="HTML",
            reply_markup=back_to_main(),
        )
        return

    # Статистика в тексте
    avg_dur = sum(r["duration_h"] for r in records) / len(records)
    avg_h = int(avg_dur)
    avg_m = int((avg_dur - avg_h) * 60)
    avg_str = f"{avg_h}ч {avg_m}м" if avg_m else f"{avg_h}ч"

    username = callback.from_user.full_name or "пользователь"
    chart_bytes = _build_chart(records, username)

    caption = (
        f"📊 <b>Статистика сна за 7 дней</b>\n\n"
        f"📝 Записей: <b>{len(records)}</b>\n"
        f"⏱ Средняя длительность: <b>{avg_str}</b>\n\n"
        f"<i>Цвет столбца = оценка самочувствия</i>"
    )

    photo = BufferedInputFile(chart_bytes, filename="sleep_stats.png")

    # Отправляем фото отдельным сообщением (edit_message не поддерживает смену типа)
    await callback.message.answer_photo(
        photo=photo,
        caption=caption,
        parse_mode="HTML",
        reply_markup=back_to_main(),
    )

    # Удаляем предыдущее сообщение (чтобы не было «мусора»)
    try:
        await callback.message.delete()
    except Exception:
        pass
