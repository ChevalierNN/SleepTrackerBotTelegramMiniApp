import aiosqlite
from datetime import date, datetime

DB_PATH = "sleep_tracker.db"


async def init_db() -> None:
    """Создаёт таблицу при первом запуске."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS sleep_records (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id     INTEGER NOT NULL,
                record_date TEXT    NOT NULL,
                sleep_time  TEXT    NOT NULL,
                wake_time   TEXT    NOT NULL,
                duration_h  REAL    NOT NULL,
                quality     TEXT    NOT NULL,
                created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
            )
        """)
        await db.commit()


async def save_record(
    user_id: int,
    sleep_time: str,
    wake_time: str,
    duration_h: float,
    quality: str,
) -> None:
    """Сохраняет одну запись о сне."""
    today = date.today().isoformat()
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            INSERT INTO sleep_records (user_id, record_date, sleep_time, wake_time, duration_h, quality)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (user_id, today, sleep_time, wake_time, duration_h, quality),
        )
        await db.commit()


async def get_week_records(user_id: int) -> list[dict]:
    """
    Возвращает записи за последние 7 дней для конкретного пользователя.
    Сортировка по дате по возрастанию.
    """
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """
            SELECT record_date, sleep_time, wake_time, duration_h, quality
            FROM sleep_records
            WHERE user_id = ?
              AND record_date >= date('now', '-6 days')
            ORDER BY record_date ASC
            """,
            (user_id,),
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]


async def get_all_records(user_id: int) -> list[dict]:
    """Возвращает все записи пользователя (для отладки)."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM sleep_records WHERE user_id = ? ORDER BY record_date DESC",
            (user_id,),
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
