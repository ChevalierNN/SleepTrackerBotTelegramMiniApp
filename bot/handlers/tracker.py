"""
Sleep tracker FSM handler.
Flow: sleep_time → wake_time → quality → save to DB
"""

from datetime import datetime, timedelta

from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from database import save_record
from keyboards import quality_keyboard, back_to_main
from states import SleepTracker
from utils.sleep_calc import parse_time, QUALITY_LABELS

router = Router(name="tracker")


# ── Старт трекера ────────────────────────────────────────────────────────────

@router.callback_query(F.data == "menu_tracker")
async def tracker_start(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(SleepTracker.waiting_sleep_time)
    await callback.message.edit_text(
        "📝 <b>Запись сна — шаг 1 из 3</b>\n\n"
        "🛌 Во сколько ты <b>лёг(легла) спать</b>?\n\n"
        "Введи время в формате <b>ЧЧ:ММ</b>\n"
        "Например: <code>23:30</code> или <code>01:00</code>",
        parse_mode="HTML",
        reply_markup=back_to_main(),
    )
    await callback.answer()


# ── Шаг 1: время отхода ─────────────────────────────────────────────────────

@router.message(SleepTracker.waiting_sleep_time)
async def tracker_got_sleep_time(message: Message, state: FSMContext) -> None:
    t = parse_time(message.text or "")
    if t is None:
        await message.answer(
            "❌ Неверный формат. Введи время в виде <b>ЧЧ:ММ</b>, например <code>23:30</code>",
            parse_mode="HTML",
        )
        return

    await state.update_data(sleep_time=t.strftime("%H:%M"))
    await state.set_state(SleepTracker.waiting_wake_time)
    await message.answer(
        "📝 <b>Запись сна — шаг 2 из 3</b>\n\n"
        f"✅ Время отхода: <b>{t.strftime('%H:%M')}</b>\n\n"
        "⏰ Во сколько ты <b>проснулся(проснулась)</b>?\n"
        "Введи время в формате <b>ЧЧ:ММ</b>",
        parse_mode="HTML",
        reply_markup=back_to_main(),
    )


# ── Шаг 2: время подъёма ────────────────────────────────────────────────────

@router.message(SleepTracker.waiting_wake_time)
async def tracker_got_wake_time(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    sleep_str: str = data["sleep_time"]

    wake = parse_time(message.text or "")
    if wake is None:
        await message.answer(
            "❌ Неверный формат. Введи время в виде <b>ЧЧ:ММ</b>, например <code>07:30</code>",
            parse_mode="HTML",
        )
        return

    # Рассчитываем длительность
    sleep_dt = parse_time(sleep_str)
    if sleep_dt is None:
        await message.answer("❌ Ошибка данных. Попробуй начать заново.")
        await state.clear()
        return

    if wake <= sleep_dt:
        wake += timedelta(days=1)  # сон перешёл через полночь

    duration_h = (wake - sleep_dt).total_seconds() / 3600

    await state.update_data(wake_time=wake.strftime("%H:%M"), duration_h=round(duration_h, 2))
    await state.set_state(SleepTracker.waiting_quality)

    hours = int(duration_h)
    minutes = int((duration_h - hours) * 60)
    duration_str = f"{hours}ч {minutes}м" if minutes else f"{hours}ч"

    await message.answer(
        "📝 <b>Запись сна — шаг 3 из 3</b>\n\n"
        f"✅ Лёг: <b>{sleep_str}</b>\n"
        f"✅ Встал: <b>{wake.strftime('%H:%M')}</b>\n"
        f"⏱ Продолжительность: <b>{duration_str}</b>\n\n"
        "💬 Как ты себя чувствуешь после сна?",
        parse_mode="HTML",
        reply_markup=quality_keyboard(),
    )


# ── Шаг 3: оценка качества ──────────────────────────────────────────────────

@router.callback_query(F.data.startswith("quality_"))
async def tracker_got_quality(callback: CallbackQuery, state: FSMContext) -> None:
    current_state = await state.get_state()
    if current_state != SleepTracker.waiting_quality:
        await callback.answer("Эта кнопка уже не активна.", show_alert=True)
        return

    quality_key = callback.data  # e.g. "quality_great"
    quality_label = QUALITY_LABELS.get(quality_key, quality_key)

    data = await state.get_data()
    await state.clear()

    await save_record(
        user_id=callback.from_user.id,
        sleep_time=data["sleep_time"],
        wake_time=data["wake_time"],
        duration_h=data["duration_h"],
        quality=quality_label,
    )

    hours = int(data["duration_h"])
    minutes = int((data["duration_h"] - hours) * 60)
    duration_str = f"{hours}ч {minutes}м" if minutes else f"{hours}ч"

    await callback.message.edit_text(
        "✅ <b>Запись сохранена!</b>\n\n"
        f"🛌 Лёг:         <b>{data['sleep_time']}</b>\n"
        f"⏰ Встал:        <b>{data['wake_time']}</b>\n"
        f"⏱ Длительность: <b>{duration_str}</b>\n"
        f"💬 Самочувствие: <b>{quality_label}</b>\n\n"
        "📊 Посмотреть статистику можно через кнопку <b>«Моя статистика»</b> в меню.",
        parse_mode="HTML",
        reply_markup=back_to_main(),
    )
    await callback.answer("Сохранено! 🎉")
