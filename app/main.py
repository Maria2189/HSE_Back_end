from fastapi import FastAPI
from app.routers import homework

app = FastAPI(
    title="Microlearning Platform API",
    description="Бэкенд для платформы микрообучения"
)

app.include_router(homework.router)