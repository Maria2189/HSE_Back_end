"""
Общие фикстуры для тестов.

Используется отдельная SQLite-БД в файле test_db.sqlite, чтобы не портить
основную БД. Схема для тестов создаётся через Base.metadata.create_all,
а не через alembic — это быстрее и не требует ENV-переменной.
"""
import os
os.environ.setdefault("SECRET_KEY", "test_secret_key_only_for_tests")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database.session import Base, get_db
from app.database.models import User
from app.core.security import get_password_hash, create_access_token

TEST_DB_URL = "sqlite:///./test_db.sqlite"
test_engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestSession = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    db = TestSession()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def setup_database():
    """Перед каждым тестом — чистая схема."""
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture
def db_session():
    db = TestSession()
    try:
        yield db
    finally:
        db.close()


# ------ Готовые пользователи и заголовки ------

def _make_user(db, email: str, role: str = "user", password: str = "password123") -> User:
    user = User(
        email=email,
        hashed_password=get_password_hash(password),
        first_name="Имя",
        last_name="Фамилия",
        role=role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _auth_header(email: str, role: str) -> dict:
    token = create_access_token({"sub": email, "role": role})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_user(db_session):
    return _make_user(db_session, "admin@example.com", role="admin")


@pytest.fixture
def regular_user(db_session):
    return _make_user(db_session, "user@example.com", role="user")


@pytest.fixture
def second_user(db_session):
    return _make_user(db_session, "user2@example.com", role="user")


@pytest.fixture
def admin_headers(admin_user):
    return _auth_header(admin_user.email, "admin")


@pytest.fixture
def user_headers(regular_user):
    return _auth_header(regular_user.email, "user")


@pytest.fixture
def second_user_headers(second_user):
    return _auth_header(second_user.email, "user")


# ------ Хелперы для подготовки данных ------

@pytest.fixture
def make_category(client, admin_headers):
    """Фабрика категорий через API."""
    def _make(name="Программирование", description="Курсы по разработке"):
        res = client.post(
            "/categories/",
            json={"name": name, "description": description},
            headers=admin_headers,
        )
        assert res.status_code == 201, res.text
        return res.json()
    return _make


@pytest.fixture
def make_course(client, admin_headers, make_category):
    """Фабрика курсов: создаёт категорию (один раз на тест) и курс."""
    state = {"default_category_id": None}

    def _make(title="Python с нуля", price="100.00", category_id=None):
        if category_id is None:
            if state["default_category_id"] is None:
                state["default_category_id"] = make_category()["id"]
            category_id = state["default_category_id"]
        res = client.post(
            "/courses/",
            json={
                "title": title,
                "description": f"Описание курса {title}",
                "price": price,
                "category_id": category_id,
            },
            headers=admin_headers,
        )
        assert res.status_code == 201, res.text
        return res.json()
    return _make


@pytest.fixture
def make_topic(client, admin_headers):
    """Фабрика тем."""
    def _make(course_id, title="Введение", content="Текст темы", order=0, is_free=False):
        res = client.post(
            f"/courses/{course_id}/topics",
            json={"title": title, "content": content, "order": order, "is_free": is_free},
            headers=admin_headers,
        )
        assert res.status_code == 201, res.text
        return res.json()
    return _make
