import asyncio
import json
import logging
import sys
import io
from datetime import datetime, timedelta

from aiogram import Bot, Dispatcher, F
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command
from aiogram.types import (
    Message, CallbackQuery,
    MenuButtonWebApp, WebAppInfo,
)
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession

from config import BOT_TOKEN, WEBAPP_URL
from database import init_db, save_record
from keyboards import main_menu
from handlers import calculator, tracker, stats
from server import run_server

# UTF-8 
_utf8_stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=_utf8_stdout,
)
logger = logging.getLogger(__name__)


# Авто-прокси из реестра Windows 

def _get_windows_proxy() -> str | None:
    if sys.platform != "win32":
        return None
    try:
        import winreg
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Internet Settings",
        )
        enabled, _ = winreg.QueryValueEx(key, "ProxyEnable")
        if enabled:
            server, _ = winreg.QueryValueEx(key, "ProxyServer")
            proxy = f"http://{server}" if not server.startswith("http") else server
            logger.info("Using Windows system proxy: %s", proxy)
            return proxy
    except Exception:
        pass
    return None


# Startup hook 

async def on_startup(bot: Bot) -> None:
    await init_db()
    me = await bot.get_me()
    logger.info("Bot started: @%s", me.username)

    try:
        await bot.set_chat_menu_button(
            menu_button=MenuButtonWebApp(
                text="📱 Трекер",
                web_app=WebAppInfo(url=WEBAPP_URL),
            )
        )
        logger.info("Menu button set → %s", WEBAPP_URL)
    except Exception as e:
        logger.warning("Could not set menu button: %s", e)


# Общие хэндлеры 

async def cmd_start(message: Message) -> None:
    name = message.from_user.first_name if message.from_user else "друг"
    await message.answer(
        f"🌙 Привет, <b>{name}</b>!\n\n"
        "Я — твой личный <b>трекер сна</b>. Умею:\n"
        "• 📱 Полноценный Mini App с графиками и логированием\n"
        "• 🧮 Калькулятор циклов сна прямо в чате\n"
        "• 📊 Статистика за неделю в чате\n\n"
        "Нажми <b>«📱 Открыть Mini App»</b> для полного интерфейса\n"
        "или выбери другой раздел:",
        parse_mode="HTML",
        reply_markup=main_menu(),
    )


async def cmd_menu(message: Message) -> None:
    await message.answer(
        "🏠 <b>Главное меню</b>\n\nВыбери раздел:",
        parse_mode="HTML",
        reply_markup=main_menu(),
    )


async def back_to_main_handler(callback: CallbackQuery) -> None:
    await callback.message.edit_text(
        "🏠 <b>Главное меню</b>\n\nВыбери раздел:",
        parse_mode="HTML",
        reply_markup=main_menu(),
    )
    await callback.answer()


# Mini App data handler

async def handle_webapp_data(message: Message) -> None:
    """
    Резервный канал: Mini App может отправлять данные через sendData().
    Основной путь — POST /api/sleep на сервер.
    """
    try:
        payload = json.loads(message.web_app_data.data)
    except (json.JSONDecodeError, AttributeError):
        await message.answer("❌ Не удалось прочитать данные из Mini App.")
        return

    if payload.get("action") != "save_sleep":
        return

    sleep_time: str   = payload.get("sleep_time", "")
    wake_time:  str   = payload.get("wake_time",  "")
    duration_h: float = float(payload.get("duration_h", 0))
    quality:    str   = payload.get("quality", "—")

    await save_record(
        user_id=message.from_user.id,
        sleep_time=sleep_time,
        wake_time=wake_time,
        duration_h=round(duration_h, 2),
        quality=quality,
    )

    h, m = int(duration_h), int((duration_h % 1) * 60)
    dur_str = f"{h}ч {m}м" if m else f"{h}ч"

    await message.answer(
        f"✅ <b>Запись сохранена!</b>\n\n"
        f"🛏 Лёг: <b>{sleep_time}</b>\n"
        f"⏰ Встал: <b>{wake_time}</b>\n"
        f"⏱ Длительность: <b>{dur_str}</b>\n"
        f"💬 Самочувствие: <b>{quality}</b>",
        parse_mode="HTML",
        reply_markup=main_menu(),
    )


# Сборка и запуск 

async def main() -> None:
    proxy   = _get_windows_proxy()
    session = AiohttpSession(proxy=proxy) if proxy else AiohttpSession()

    bot = Bot(
        token=BOT_TOKEN,
        session=session,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=MemoryStorage())

    dp.startup.register(on_startup)

    # Общие хэндлеры
    dp.message.register(cmd_start, CommandStart())
    dp.message.register(cmd_menu, Command("menu"))
    dp.message.register(handle_webapp_data, F.web_app_data)
    dp.callback_query.register(back_to_main_handler, F.data == "back_main")

    # Роутеры модулей 
    dp.include_router(calculator.router)
    dp.include_router(tracker.router)
    dp.include_router(stats.router)

    logger.info("Starting bot + Mini App server on port 8085...")
    await asyncio.gather(
        dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types()),
        run_server(),
    )


if __name__ == "__main__":
    asyncio.run(main())
