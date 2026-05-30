"""Тесты корневых эндпоинтов и общих сценариев безопасности."""


def test_root(client):
    res = client.get("/")
    assert res.status_code == 200
    assert "Welcome" in res.json()["message"]


def test_health(client):
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


def test_invalid_jwt_rejected(client, make_course):
    """Гарбадж-токен не даёт доступа к защищённым эндпоинтам."""
    course = make_course()
    res = client.post(
        f"/courses/{course['id']}/purchase",
        headers={"Authorization": "Bearer not.a.real.token"},
    )
    assert res.status_code == 401


def test_sql_injection_in_login_safe(client):
    """SQLAlchemy ORM параметризует все запросы; попытка SQL-инъекции просто получит 401."""
    res = client.post(
        "/auth/login",
        data={"username": "' OR 1=1 --", "password": "x"},
    )
    assert res.status_code == 401


def test_sql_injection_in_category_filter_safe(client):
    """Параметр query-строки с инъекцией должен не сработать как код."""
    res = client.get("/courses/?category_id=1;DROP TABLE users--")
    assert res.status_code in (200, 422)
