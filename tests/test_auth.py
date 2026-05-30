"""Функциональные тесты сервиса авторизации."""


def _register_payload(email="new@example.com", password="password123"):
    return {
        "email": email,
        "password": password,
        "first_name": "Иван",
        "last_name": "Иванов",
    }


# ---------- /auth/register ----------

def test_register_success(client):
    res = client.post("/auth/register", json=_register_payload())
    assert res.status_code == 201
    data = res.json()
    assert "access_token" in data and "refresh_token" in data
    assert data["token_type"] == "bearer"


def test_register_duplicate_email(client):
    client.post("/auth/register", json=_register_payload(email="dup@example.com"))
    res = client.post("/auth/register", json=_register_payload(email="dup@example.com"))
    assert res.status_code == 400
    assert res.json()["detail"] == "Email already registered"


def test_register_invalid_email(client):
    res = client.post("/auth/register", json=_register_payload(email="not-an-email"))
    assert res.status_code == 422


def test_register_short_password(client):
    res = client.post("/auth/register", json=_register_payload(password="12"))
    assert res.status_code == 422


def test_register_missing_names(client):
    res = client.post(
        "/auth/register",
        json={"email": "x@example.com", "password": "password123"},
    )
    assert res.status_code == 422


# ---------- /auth/login ----------

def test_login_success(client):
    client.post("/auth/register", json=_register_payload(email="lg@example.com"))
    res = client.post(
        "/auth/login",
        data={"username": "lg@example.com", "password": "password123"},
    )
    assert res.status_code == 200
    assert "access_token" in res.json()


def test_login_wrong_password(client):
    client.post("/auth/register", json=_register_payload(email="lg@example.com"))
    res = client.post(
        "/auth/login",
        data={"username": "lg@example.com", "password": "wrongone"},
    )
    assert res.status_code == 401


def test_login_unknown_user(client):
    res = client.post(
        "/auth/login",
        data={"username": "ghost@example.com", "password": "whatever"},
    )
    assert res.status_code == 401


# ---------- /auth/refresh ----------

def test_refresh_token_success(client):
    reg = client.post("/auth/register", json=_register_payload(email="ref@example.com"))
    refresh = reg.json()["refresh_token"]
    res = client.post("/auth/refresh", json={"refresh_token": refresh})
    assert res.status_code == 200
    assert "access_token" in res.json()


def test_refresh_token_invalid(client):
    res = client.post("/auth/refresh", json={"refresh_token": "garbage.token.value"})
    assert res.status_code == 401


def test_refresh_with_access_token_rejected(client):
    """Access-токен не должен приниматься на /refresh."""
    reg = client.post("/auth/register", json=_register_payload(email="r2@example.com"))
    access = reg.json()["access_token"]
    res = client.post("/auth/refresh", json={"refresh_token": access})
    assert res.status_code == 401


# ---------- /auth/change-password ----------

def test_change_password_success(client):
    reg = client.post("/auth/register", json=_register_payload(email="cp@example.com"))
    token = reg.json()["access_token"]
    res = client.post(
        "/auth/change-password",
        json={"old_password": "password123", "new_password": "newpassword456"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 204

    # Старый пароль больше не работает
    res2 = client.post(
        "/auth/login",
        data={"username": "cp@example.com", "password": "password123"},
    )
    assert res2.status_code == 401

    # Новый пароль работает
    res3 = client.post(
        "/auth/login",
        data={"username": "cp@example.com", "password": "newpassword456"},
    )
    assert res3.status_code == 200


def test_change_password_wrong_old(client):
    reg = client.post("/auth/register", json=_register_payload(email="cp2@example.com"))
    token = reg.json()["access_token"]
    res = client.post(
        "/auth/change-password",
        json={"old_password": "wrong", "new_password": "newpassword456"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 400


def test_change_password_requires_auth(client):
    res = client.post(
        "/auth/change-password",
        json={"old_password": "a", "new_password": "abcdef"},
    )
    assert res.status_code == 401


# ---------- /auth/me ----------

def test_me_returns_profile(client):
    reg = client.post("/auth/register", json=_register_payload(email="me@example.com"))
    token = reg.json()["access_token"]
    res = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    data = res.json()
    assert data["email"] == "me@example.com"
    assert data["role"] == "user"
    assert data["first_name"] == "Иван"


def test_me_requires_auth(client):
    assert client.get("/auth/me").status_code == 401
