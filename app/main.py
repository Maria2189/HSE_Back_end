from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.routers import appeals, students, auth
from app.database.session import engine
from app.database import models

from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from redis import asyncio as aioredis
from app.core.config import settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    redis = aioredis.from_url(settings.REDIS_URL, encoding="utf8", decode_responses=True)
    FastAPICache.init(RedisBackend(redis), prefix="fastapi-cache")
    yield

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Microlearning Platform API", lifespan=lifespan)

app.include_router(appeals.router)
app.include_router(students.router)
app.include_router(auth.router)

@app.get("/")
def root():
    return {"message": "Welcome to Microlearning Platform API"}