"""
Calculator handler: two modes
  1. calc_sleep_now  — user sleeps NOW, shows 4 optimal wake-up times
  2. calc_alarm      — user enters alarm time, shows optimal bedtimes
"""

from datetime import datetime

from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from keyboards import calculator_menu, back_to_calculator, back_to_main
from states import AlarmCalculator
from utils.sleep_calc import get_wake_times, get_sleep_times, parse_time

router = Router(name="calculator")

# ── Меню калькулятора ────────────────────────────────────────────────────────

@router.callback_query(F.data == "menu_calculator")
async def show_calculator_menu(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.message.edit_text(
        "🧮 <b>Калькулятор циклов сна</b>\n\n"
        "Один цикл сна длится <b>~90 минут</b>.\n"
        "Выбери режим:",
        reply_markup=calculator_menu(),
        parse_mode="HTML",
    )
    await callback.answer()


# ── Режим 1: Лечь сейчас ────────────────────────────────────────────────────

@router.callback_query(F.data == "calc_sleep_now")
async def calc_sleep_now(callback: CallbackQuery) -> None:
    now = datetime.now()
    times = get_wake_times(now)

    lines = [
        f"😴 <b>Ложишься сейчас</b> ({now.strftime('%H:%M')})\n"
        f"⏰ Засыпание примерно в <b>{(now.replace(second=0, microsecond=0)).strftime('%H:%M')}</b> + 15 мин\n\n"
        "🌙 <b>Оптимальные времена пробуждения:</b>\n"
    ]

    medals = ["🥇", "🥈", "🥉", "✨"]
    for i, item in enumerate(times):
        medal = medals[i] if i < len(medals) else "✅"
        wake_str = item["wake_time"].strftime("%H:%M")
        lines.append(
            f"{medal} <b>{wake_str}</b>  — {item['cycles']} цикла ({item['duration']})"
        )

    lines.append(
        "\n💡 <i>Рекомендуется 5–6 циклов (7.5–9 ч) для полноценного восстановления.</i>"
    )

    await callback.message.edit_text(
        "\n".join(lines),
        reply_markup=back_to_calculator(),
        parse_mode="HTML",
    )
    await callback.answer()


# ── Режим 2: Под будильник ───────────────────────────────────────────────────

@router.callback_query(F.data == "calc_alarm")
async def calc_alarm_start(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(AlarmCalculator.waiting_alarm_time)
    await callback.message.edit_text(
        "⏰ <b>Калькулятор по будильнику</b>\n\n"
        "Введи время будильника в формате <b>ЧЧ:ММ</b>\n"
        "Например: <code>07:00</code> или <code>6:30</code>",
        reply_markup=back_to_calculator(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(AlarmCalculator.waiting_alarm_time)
async def calc_alarm_result(message: Message, state: FSMContext) -> None:
    now = datetime.now()
    alarm = parse_time(message.text or "", now)

    if alarm is None:
        await message.answer(
            "❌ Неверный формат. Введи время в формате <b>ЧЧ:ММ</b>, например <code>07:00</code>",
            parse_mode="HTML",
        )
        return

    # Если будильник уже прошёл — считаем на завтра
    if alarm <= now:
        from datetime import timedelta
        alarm += timedelta(days=1)

    await state.clear()
    times = get_sleep_times(alarm)

    lines = [
        f"⏰ <b>Будильник в {alarm.strftime('%H:%M')}</b>\n\n"
        "🛏 <b>Ложись спать в одно из этих времён:</b>\n"
    ]

    medals = ["🥇", "🥈", "🥉", "✨"]
    for i, item in enumerate(times):
        medal = medals[i] if i < len(medals) else "✅"
        sleep_str = item["sleep_time"].strftime("%H:%M")
        lines.append(
            f"{medal} <b>{sleep_str}</b>  — {item['cycles']} цикла ({item['duration']})"
        )

    lines.append(
        "\n💡 <i>+15 мин на засыпание уже учтены.</i>"
    )

    await message.answer(
        "\n".join(lines),
        reply_markup=back_to_calculator(),
        parse_mode="HTML",
    )
