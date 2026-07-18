"""
keyboards.py — Все inline-клавиатуры бота.
"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from config import WEBAPP_URL


# ── Главное меню ──────────────────────────────────────────────
def main_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        # Mini App — полный трекер в красивом UI
        [
            InlineKeyboardButton(
                text="📱 Открыть Mini App",
                web_app=WebAppInfo(url=WEBAPP_URL),
            ),
        ],
        # Текстовый калькулятор — работает без ngrok
        [InlineKeyboardButton(text="🧮 Калькулятор (в чате)", callback_data="menu_calculator")],
        # Текстовая статистика — работает без ngrok
        [InlineKeyboardButton(text="📋 Статистика (в чате)", callback_data="menu_stats")],
    ])


# ── Калькулятор ───────────────────────────────────────────────
def calculator_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="😴 Лечь сейчас",  callback_data="calc_sleep_now")],
        [InlineKeyboardButton(text="⏰ Под будильник", callback_data="calc_alarm")],
        [InlineKeyboardButton(text="◀️ Назад",         callback_data="back_main")],
    ])


def back_to_calculator() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ К калькулятору", callback_data="menu_calculator")],
        [InlineKeyboardButton(text="🏠 Главное меню",   callback_data="back_main")],
    ])


# ── Трекер ────────────────────────────────────────────────────
def quality_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="⚡ Бодр",        callback_data="quality_great"),
            InlineKeyboardButton(text="😊 Выспался",    callback_data="quality_good"),
        ],
        [
            InlineKeyboardButton(text="😐 Не выспался", callback_data="quality_poor"),
            InlineKeyboardButton(text="💀 Разбит",      callback_data="quality_awful"),
        ],
    ])


def back_to_main() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="back_main")],
    ])
