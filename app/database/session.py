"""
Настройка SQLAlchemy: движок, фабрика сессий и зависимость get_db.

По умолчанию используется SQLite (удобно для локальной разработки и тестов).
Через переменную окружения DATABASE_URL можно переключиться на PostgreSQL,
что и делает docker-compose в продакшен-варианте.
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./microlearning.db")

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args, future=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """FastAPI-зависимость: открывает сессию на запрос и гарантированно закрывает."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
