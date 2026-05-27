import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database.session import Base, get_db
from app.core.security import create_access_token

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_db.sqlite"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c

# ==========================================
# ФИКСТУРЫ ДЛЯ АВТОРИЗАЦИИ
# ==========================================
@pytest.fixture
def admin_headers():
    """Генерирует токен с правами admin для тестов"""
    token = create_access_token(data={"sub": "admin@test.com", "role": "admin"})
    return {"Authorization": f"Bearer {token}"}
    
@pytest.fixture
def readonly_headers():
    """Генерирует токен с правами readonly для тестов"""
    token = create_access_token(data={"sub": "user@test.com", "role": "readonly"})
    return {"Authorization": f"Bearer {token}"}

# ==========================================
# ЭНДПОИНТ 1: /auth/register
# ==========================================
def test_register_success(client):
    """Успешная регистрация пользователя"""
    response = client.post(
        "/auth/register",
        json={"email": "test@example.com", "password": "strongpassword"}
    )
    assert response.status_code == 201
    assert "access_token" in response.json()
    assert "refresh_token" in response.json()

def test_register_duplicate_email(client):
    """Ошибка: регистрация с уже существующим email"""
    client.post("/auth/register", json={"email": "test@example.com", "password": "pass"})
    response = client.post("/auth/register", json={"email": "test@example.com", "password": "pass"})
    
    assert response.status_code == 400
    assert response.json()["detail"] == "Email already registered"

# ==========================================
# ЭНДПОИНТ 2: /auth/login
# ==========================================
def test_login_success(client):
    """Успешная авторизация (возврат токена)"""
    client.post("/auth/register", json={"email": "login@example.com", "password": "mypassword"})
    
    response = client.post(
        "/auth/login",
        data={"username": "login@example.com", "password": "mypassword"} 
    )
    assert response.status_code == 200
    assert "access_token" in response.json()

def test_login_wrong_password(client):
    """Ошибка: неверный пароль при авторизации"""
    client.post("/auth/register", json={"email": "login@example.com", "password": "mypassword"})
    response = client.post(
        "/auth/login",
        data={"username": "login@example.com", "password": "wrongpassword"}
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect email or password"

# ==========================================
# ЭНДПОИНТ 3: /auth/logout
# ==========================================
def test_logout_success(client):
    """Успешный выход из системы"""
    response = client.post("/auth/logout")
    assert response.status_code == 200
    assert "Successfully logged out" in response.json()["message"]

def test_logout_wrong_method(client):
    """Ошибка: использование неверного HTTP-метода"""
    response = client.get("/auth/logout")
    assert response.status_code == 405

# ==========================================
# ЭНДПОИНТ 4: Корневой /
# ==========================================
def test_root_success(client):
    """Успешное получение приветственного сообщения"""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to Microlearning Platform API"}

def test_root_post_method_not_allowed(client):
    """Ошибка: POST-запрос на GET-эндпоинт"""
    response = client.post("/") 
    assert response.status_code == 405

# ==========================================
# ЭНДПОИНТ 5: /appeals/
# ==========================================
def test_create_appeal_unauthorized(client):
    """Ошибка: попытка создать обращение без авторизации"""
    appeal_data = {
        "surname": "Иванов",
        "name": "Иван",
        "dob": "2000-01-01",
        "phone": "+79991234567",
        "email": "ivan@example.com",
        "reasons": ["нет доступа к сети"],
        "problem_discovery_time": "2026-05-20T12:00:00Z"
    }
    response = client.post("/appeals/", json=appeal_data)
    assert response.status_code == 401

def test_create_appeal_bad_data(client):
    """Ошибка: провал валидации Pydantic (фамилия латиницей вместо кириллицы)"""
    client.post("/auth/register", json={"email": "user@example.com", "password": "123"})
    login_res = client.post("/auth/login", data={"username": "user@example.com", "password": "123"})
    token = login_res.json()["access_token"]

    appeal_data = {
        "surname": "Ivanov",
        "name": "Иван",
        "dob": "2000-01-01",
        "phone": "+79991234567",
        "email": "ivan@example.com",
        "reasons": ["нет доступа к сети"],
        "problem_discovery_time": "2026-05-20T12:00:00Z"
    }
    
    response = client.post(
        "/appeals/", 
        json=appeal_data, 
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 422
    assert "Значение должно начинаться с заглавной буквы, содержать только кириллицу" in response.text

# ==========================================
# ЭНДПОИНТЫ 6: /students/ (Бизнес-логика)
# ==========================================
def test_create_student_success(client, admin_headers):
    """Успешное создание студента (роль admin)"""
    student_data = {
        "first_name": "Мария",
        "last_name": "Иванова",
        "faculty": "ПИ",
        "course": "Python",
        "score": 95
    }
    response = client.post("/students/", json=student_data, headers=admin_headers)
    assert response.status_code == 201
    
    data = response.json()
    assert data["first_name"] == "Мария"
    assert data["course"] == "Python"
    assert "id" in data

def test_create_student_forbidden(client, readonly_headers):
    """Ошибка: попытка создать студента с правами readonly (проверка RBAC)"""
    student_data = {
        "first_name": "Иван",
        "last_name": "Петров",
        "faculty": "ПИ",
        "course": "Java",
        "score": 80
    }
    response = client.post("/students/", json=student_data, headers=readonly_headers)
    assert response.status_code == 403
    assert response.json()["detail"] == "Operation not permitted"

def test_read_student_success(client, admin_headers):
    """Успешное получение данных студента"""
    create_res = client.post(
        "/students/", 
        json={"first_name": "Олег", "last_name": "Попов", "faculty": "БИ", "course": "Математика", "score": 75}, 
        headers=admin_headers
    )
    student_id = create_res.json()["id"]

    response = client.get(f"/students/{student_id}", headers=admin_headers)
    assert response.status_code == 200
    assert response.json()["first_name"] == "Олег"
    assert response.json()["score"] == 75

def test_update_student_success(client, admin_headers):
    """Успешное обновление баллов студента (PATCH)"""
    create_res = client.post(
        "/students/", 
        json={"first_name": "Анна", "last_name": "Смирнова", "faculty": "ФКН", "course": "БД", "score": 60}, 
        headers=admin_headers
    )
    student_id = create_res.json()["id"]

    update_res = client.patch(f"/students/{student_id}", json={"score": 100}, headers=admin_headers)
    assert update_res.status_code == 200
    assert update_res.json()["score"] == 100
    assert update_res.json()["first_name"] == "Анна"

def test_delete_student_success(client, admin_headers):
    """Успешное удаление студента из БД"""
    create_res = client.post(
        "/students/", 
        json={"first_name": "Тест", "last_name": "Удаляемый", "faculty": "ПИ", "course": "C++", "score": 50}, 
        headers=admin_headers
    )
    student_id = create_res.json()["id"]

    del_res = client.delete(f"/students/{student_id}", headers=admin_headers)
    assert del_res.status_code == 204

    get_res = client.get(f"/students/{student_id}", headers=admin_headers)
    assert get_res.status_code == 404