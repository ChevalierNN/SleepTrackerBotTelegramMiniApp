# Sleep Calculator & Tracker Bot (Telegram Mini App)

> Умный бот и Telegram Mini App для калькуляции фаз сна, трекинга ночного отдыха и анализа самочувствия. Рассчитан на 90-минутные циклы сна для легкого пробуждения.

---

## Скриншоты 

### Telegram Mini App 
<p align="left">
<img width="344" height="677" alt="photo_2026-08-05_18-53-39" src="https://github.com/user-attachments/assets/9615f9ae-360f-43b1-aaa0-edb5c19de47c" />
<img width="341" height="678" alt="photo_2026-08-05_18-48-17" src="https://github.com/user-attachments/assets/1afbf791-eb64-49ab-a22f-5adba9bf593a" />
<img width="349" height="674" alt="image" src="https://github.com/user-attachments/assets/2cd0b817-092f-4f15-8e25-89774abc6d1b" />
<img width="315" height="692" alt="image" src="https://github.com/user-attachments/assets/efbabcfe-7c6c-43d4-9876-78fde22fe860" />


</p>

### Telegram Bot
<p align="left">
  <img width="365" height="302" alt="image" src="https://github.com/user-attachments/assets/88c0f78d-6c0c-4085-be9f-840c5e7611bb" />
  <img width="294" height="266" alt="image" src="https://github.com/user-attachments/assets/162772da-f5b6-479f-a9c1-4b311b946fad" />
</p>


---

## Основные возможности

- **Калькулятор сна (90-минутные циклы):**
  - **«Лечь сейчас»**: Вычисляет идеальные точки пробуждения (с учетом +15 минут на засыпание).
  - **«Под будильник»**: Определяет оптимальное время для того, чтобы лечь спать к выбранному часу.
- **Запись и дневник сна:**
  - Удобный фиксатор времени засыпания и подъема.
  - Оценка состояния после пробуждения (*Бодр*, *Выспался*, *Не выспался*, *Разбит*).
- **Персональная аналитика:**
  - Гистограмма длительности сна за последние дни.
  - Круговая диаграмма качества пробуждений.
  - Вычисление среднего времени сна и тренда стабильности.
- **Двойной интерфейс:** Работайте с быстрым Mini App или через привычные кнопки внутри чата Telegram.

---

## Технологический стек

- **Backend (Telegram Bot):** Python 3 (aiogram / python-telegram-bot)
- **Web App Server:** Python (aiohttp / Flask / FastAPI в `server.py`)
- **Frontend (Mini App):** JavaScript, HTML5, CSS3 (`webapp/`)
- **База данных:** SQLite (`sleep_tracker.db`)

---

## Структура проекта

```text
Sleep_bot/
├── handlers/        # Обработчики команд и сообщений бота
├── utils/           # Вспомогательные функции (расчет циклов сна)
├── webapp/          # Frontend-интерфейс Telegram Mini App
├── config.py        # Конфигурация приложения
├── database.py      # Модель и взаимодействие с SQLite
├── keyboards.py     # Клавиатуры и Inline-кнопки бота
├── main.py          # Точка входа для запуска бота
├── server.py        # Сервер для отдачи WebApp
├── states.py        # FSM состояния пользователей
└── requirements.txt # Зависимости
