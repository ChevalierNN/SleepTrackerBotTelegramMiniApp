"""
Sleep cycle calculation logic.

A sleep cycle lasts approximately 90 minutes.
The ideal number of cycles is 5–6 (7.5–9 hours).
We add 15 minutes to fall asleep.
"""

from datetime import datetime, timedelta

CYCLE_MINUTES = 90          # длительность одного цикла сна
FALL_ASLEEP_MINUTES = 15    # среднее время засыпания
CYCLES = [3, 4, 5, 6]      # рекомендуемые варианты (4.5 – 9 ч)

QUALITY_LABELS = {
    "quality_great": "⚡ Бодр",
    "quality_good":  "😊 Выспался",
    "quality_poor":  "😐 Не выспался",
    "quality_awful": "💀 Разбит",
}


def get_wake_times(sleep_now: datetime | None = None) -> list[dict]:
    """
    Возвращает список оптимальных времён пробуждения,
    если лечь спать в момент `sleep_now` (по умолчанию — сейчас).
    """
    if sleep_now is None:
        sleep_now = datetime.now()

    fall_asleep_at = sleep_now + timedelta(minutes=FALL_ASLEEP_MINUTES)
    results = []

    for cycles in CYCLES:
        wake_at = fall_asleep_at + timedelta(minutes=cycles * CYCLE_MINUTES)
        hours = cycles * CYCLE_MINUTES // 60
        minutes = cycles * CYCLE_MINUTES % 60
        results.append({
            "cycles": cycles,
            "wake_time": wake_at,
            "duration": f"{hours}ч {minutes}м" if minutes else f"{hours}ч",
        })

    return results


def get_sleep_times(alarm_time: datetime) -> list[dict]:
    """
    Возвращает список оптимальных времён отхода ко сну
    для пробуждения по будильнику в `alarm_time`.
    """
    results = []

    for cycles in reversed(CYCLES):
        sleep_duration = timedelta(minutes=cycles * CYCLE_MINUTES + FALL_ASLEEP_MINUTES)
        sleep_at = alarm_time - sleep_duration
        hours = cycles * CYCLE_MINUTES // 60
        minutes = cycles * CYCLE_MINUTES % 60
        results.append({
            "cycles": cycles,
            "sleep_time": sleep_at,
            "duration": f"{hours}ч {minutes}м" if minutes else f"{hours}ч",
        })

    return results


def parse_time(time_str: str, base_date: datetime | None = None) -> datetime | None:
    """
    Парсит строку ЧЧ:ММ в datetime, используя дату `base_date` (по умолчанию сегодня).
    Если время уже прошло сегодня — берёт завтра (актуально для будильника).
    Возвращает None при неверном формате.
    """
    time_str = time_str.strip()
    for fmt in ("%H:%M", "%H.%M"):
        try:
            t = datetime.strptime(time_str, fmt)
            base = base_date or datetime.now()
            result = base.replace(hour=t.hour, minute=t.minute, second=0, microsecond=0)
            return result
        except ValueError:
            continue
    return None
