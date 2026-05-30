# Microlearning Platform API

Платформа для микрообучения — итоговый проект по дисциплине «Разработка веб-сервисов и приложений».

Сервис реализует **Тему 3** из списка итоговых проектов: каталог курсов, темы (уроки) с разделением на платные и бесплатные, систему лайков и статистики, покупку курсов и личный кабинет пользователя — с ролевой моделью доступа и защитой от SQL-инъекций средствами SQLAlchemy ORM.

---

## Стек

| Слой | Технология |
|---|---|
| Язык | Python 3.11 |
| Фреймворк | FastAPI |
| ORM | SQLAlchemy 2.0 |
| Миграции | Alembic |
| Валидация | Pydantic v2 |
| БД | PostgreSQL 16 (Docker) / SQLite (локально) |
| Кеш | Redis 7 + fastapi-cache2 |
| Авторизация | OAuth2 + JWT (access/refresh), bcrypt |
| Тесты | pytest, pytest-cov, TestClient |
| Контейнеризация | Docker, Docker Compose |

---

## Структура проекта

```
HSE_Back_end-main/
├── alembic/                       # миграции БД
│   ├── versions/                  # папка для хранения файлов миграций
│   ├── script.py.mako             # шаблон Alembic для генерации новых файлов миграций 
│   └── env.py                     # скрипт для связи Alembic с БД и моделями SQLAlchemy
├── alembic.ini                    # конфигурационный файл Alembic
├── app/                           # главная директория с бизнес-логикой
│   ├── core/                      # ядро безопасности
│   │   ├── config.py              # pydantic-settings: ENV-переменные
│   │   ├── security.py            # bcrypt, JWT access/refresh
│   │   └── dependencies.py        # RBAC (RoleChecker), get_current_user
│   ├── database/                  # работа с БД
│   │   ├── session.py             # engine, SessionLocal, get_db
│   │   └── models.py              # SQLAlchemy-модели в 3НФ
│   ├── schemas/                   # Pydantic-схемы (auth/categories/courses/topics)
│   ├── services/                  # бизнес-логика, отделённая от роутеров
│   ├── routers/                   # FastAPI-маршруты по доменам
│   └── main.py                    # точка входа, создание экземпляра FastAPI, подключение роутеров, настройка CORS и middleware
├── tests/                         # pytest-функциональные тесты (97% покрытия)
├── Dockerfile
├── docker-compose.yml             # web + postgres + redis
├── requirements.txt
├── make_admin.py                  # CLI для создания администратора
├── .env
└── README.md
```

---

## Модель данных (3НФ)

| Таблица | Назначение |
|---|---|
| `users` | пользователи (email, имя/фамилия, hashed_password, role) |
| `categories` | категории курсов |
| `courses` | курсы (название, цена, FK → categories, FK → users.author_id) |
| `topics` | темы курса (FK → courses, content, order, is_free) |
| `purchases` | покупки (FK → users, FK → courses) — m:n с датой |
| `likes` | лайки (FK → users, FK → courses) — m:n |

Атрибуты атомарны (1НФ), все неключевые поля зависят только от первичного ключа (2НФ), транзитивных зависимостей нет (3НФ): имя категории хранится только в `categories`, а счётчики лайков/студентов вычисляются агрегатами, а не дублируются в `courses`.

UNIQUE-ограничения: `users.email`, `categories.name`, `(topics.course_id, topics.order)`, `(purchases.user_id, purchases.course_id)`, `(likes.user_id, likes.course_id)`.

---

## Эндпоинты (28 шт.)

### Авторизация
- `POST /auth/register` — регистрация (любой)
- `POST /auth/login` — OAuth2-форма (email + password)
- `POST /auth/refresh` — обновление токенов по refresh
- `POST /auth/change-password` — смена пароля (auth)
- `GET /auth/me` — текущий пользователь

### Категории
- `GET /categories/` — публичный список (с пагинацией, кешируется в Redis на 60 с)
- `GET /categories/{id}`
- `POST/PATCH/DELETE /categories/...` — только admin

### Курсы
- `GET /courses/` — каталог с пагинацией и фильтром `?category_id=`
- `GET /courses/{id}` — страница курса: метаинформация + темы (с раскрытием контента в зависимости от роли и факта покупки)
- `POST/PATCH/DELETE /courses/...` — только admin
- `POST /courses/{id}/like` / `DELETE /courses/{id}/like` — идемпотентный лайк (auth)
- `POST /courses/{id}/purchase` — покупка курса (auth)
- `GET /courses/{id}/stats` — лайки + студенты (кеш Redis 30 с)

### Темы
- `GET /courses/{id}/topics`
- `POST /courses/{id}/topics` — admin
- `GET /topics/{id}` — содержимое темы (free для всех auth, paid — только купившим/admin)
- `PATCH /topics/{id}` / `DELETE /topics/{id}` — admin

### Личный кабинет
- `GET /me/courses` — купленные курсы текущего пользователя

Полная интерактивная документация — `/docs` (Swagger UI) и `/redoc`.

---

## Запуск через Docker

> тут и далее команды для PowerShell для Windows!

```bash
# 1. Задайте SECRET_KEY (опционально)

# 1.1. Генерируем ключ и сохраняем его в переменную
$key = python -c "import secrets; print(secrets.token_hex(32))"
# 1.2. Записываем строку в файл принудительно в UTF-8
Set-Content -Path .env -Value "SECRET_KEY=$key" -Encoding UTF8

# 2. Собрать и поднять все контейнеры (web + PostgreSQL + Redis)
docker compose up --build
```

После старта `web` автоматически выполнит `alembic upgrade head` и поднимет uvicorn.

Доступ:
- API: http://localhost:8000
- Swagger: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

Создать администратора в работающем контейнере:
```bash
docker exec -it microlearning_api python make_admin.py admin@example.com strongPassword Админ Платформы
```

---

## Локальный запуск (без Docker)

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # Linux/Mac

pip install -r requirements.txt

# .env
export SECRET_KEY=any_long_random_string
# DATABASE_URL не задавайте — по умолчанию используется SQLite

alembic upgrade head
uvicorn app.main:app --reload
```

---

## Тесты и покрытие

```bash
$env:SECRET_KEY="test"; pytest tests/ --cov=app   
```

Тестовая база — отдельный файл `test_db.sqlite`, чтобы не пересекаться с боевыми данными. Покрытие: **97%**. Тесты проверяют валидацию Pydantic, бизнес-логику (доступ к платным темам только после покупки, идемпотентность лайков, конфликт повторной покупки), RBAC (admin vs user vs гость), и устойчивость к SQL-инъекциям в форме логина и параметрах запроса.

---

## Соответствие требованиям задания

| Требование | Реализация |
|---|---|
| FastAPI + Pydantic + SQLAlchemy + pytest + Docker + Uvicorn + Alembic + Redis | ✅ все восемь |
| Декомпозиция: routers/, schemas/, services/, core/ | ✅ реализованы |
| Регистрация / login / refresh / change-password | ✅ `app/routers/auth.py` |
| Защита от SQL-инъекций | ✅ ORM-параметризация (тесты в `test_root.py`) |
| Каталог курсов с пагинацией и фильтрами | ✅ `GET /courses/?skip&limit&category_id` |
| Бесплатная пробная + платные темы | ✅ `is_free` + `CoursePage.locked` |
| Личный кабинет | ✅ `GET /me/courses`, `GET /auth/me` |
| Лайки и статистика | ✅ `/courses/{id}/like` + `/stats` (кеш Redis) |
| Покупка курсов | ✅ `POST /courses/{id}/purchase` |
| Автотесты ≥ 90% | ✅ 97% (`pytest-cov`) |
| Docker Compose | ✅ web + postgres + redis |
| 3НФ | ✅ см. раздел «Модель данных» |
| Обработка невалидных данных | ✅ 422 на валидации, 400/404/409 на бизнес-конфликтах |

---
