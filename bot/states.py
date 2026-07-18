from aiogram.fsm.state import State, StatesGroup


class SleepTracker(StatesGroup):
    """FSM states for the sleep tracker questionnaire."""
    waiting_sleep_time = State()   # Во сколько лёг
    waiting_wake_time = State()    # Во сколько встал
    waiting_quality = State()      # Оценка самочувствия


class AlarmCalculator(StatesGroup):
    """FSM states for the alarm-based sleep calculator."""
    waiting_alarm_time = State()   # Ввод времени будильника
