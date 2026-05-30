"""
Точка входа FastAPI-приложения «Платформа микрообучения».

При старте приложения мы пытаемся инициализировать Redis-кеш через
fastapi-cache2. Если Redis недоступен (например, при запуске тестов
без поднятого сервиса) — используется in-memory backend, чтобы
декораторы @cache не падали.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError

from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend

from app.core.config import settings
from app.routers import auth, categories, courses, topics, me


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        from fastapi_cache.backends.redis import RedisBackend
        from redis import asyncio as aioredis
        redis = aioredis.from_url(settings.REDIS_URL, encoding="utf8", decode_responses=True)
        await redis.ping()
        FastAPICache.init(RedisBackend(redis), prefix="fastapi-cache")
    except Exception:
        FastAPICache.init(InMemoryBackend(), prefix="fastapi-cache")
    yield


app = FastAPI(
    title="Microlearning Platform API",
    description=(
        "Бэкенд платформы микрообучения: каталог курсов, темы, "
        "ролевая модель доступа, лайки, покупки и статистика."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(auth.router)
app.include_router(categories.router)
app.include_router(courses.router)
app.include_router(topics.router)
app.include_router(me.router)


@app.exception_handler(IntegrityError)
async def integrity_error_handler(request: Request, exc: IntegrityError):
    """
    Нарушение UNIQUE/FK-ограничений отдаём как 409 Conflict,
    чтобы клиент мог отличить конфликт данных от внутренней ошибки.
    """
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={"detail": "Database integrity constraint violated"},
    )


@app.get("/", tags=["Root"])
def root():
    return {"message": "Welcome to Microlearning Platform API", "docs": "/docs"}


@app.get("/health", tags=["Root"])
def health():
    return {"status": "ok"}
