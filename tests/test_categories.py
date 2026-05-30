"""Функциональные тесты эндпоинтов /categories."""


def test_list_categories_public(client):
    """Список категорий доступен без авторизации."""
    res = client.get("/categories/")
    assert res.status_code == 200
    assert res.json() == []


def test_create_category_admin(client, admin_headers):
    res = client.post(
        "/categories/",
        json={"name": "IT", "description": "Информационные технологии"},
        headers=admin_headers,
    )
    assert res.status_code == 201
    data = res.json()
    assert data["name"] == "IT"
    assert data["id"] > 0


def test_create_category_forbidden_for_user(client, user_headers):
    """Обычный пользователь не может создавать категории — 403 Forbidden."""
    res = client.post(
        "/categories/",
        json={"name": "IT", "description": "x"},
        headers=user_headers,
    )
    assert res.status_code == 403


def test_create_category_requires_auth(client):
    res = client.post("/categories/", json={"name": "IT"})
    assert res.status_code == 401


def test_create_category_duplicate_name(client, admin_headers, make_category):
    make_category(name="Дизайн")
    res = client.post(
        "/categories/",
        json={"name": "Дизайн"},
        headers=admin_headers,
    )
    assert res.status_code == 400


def test_create_category_empty_name(client, admin_headers):
    res = client.post(
        "/categories/",
        json={"name": ""},
        headers=admin_headers,
    )
    assert res.status_code == 422


def test_get_category_by_id(client, make_category):
    cat = make_category(name="ML")
    res = client.get(f"/categories/{cat['id']}")
    assert res.status_code == 200
    assert res.json()["name"] == "ML"


def test_get_category_not_found(client):
    assert client.get("/categories/9999").status_code == 404


def test_update_category(client, admin_headers, make_category):
    cat = make_category(name="Old")
    res = client.patch(
        f"/categories/{cat['id']}",
        json={"name": "New", "description": "Обновлено"},
        headers=admin_headers,
    )
    assert res.status_code == 200
    assert res.json()["name"] == "New"


def test_update_category_user_forbidden(client, user_headers, make_category):
    cat = make_category()
    res = client.patch(
        f"/categories/{cat['id']}",
        json={"name": "Hack"},
        headers=user_headers,
    )
    assert res.status_code == 403


def test_delete_category(client, admin_headers, make_category):
    cat = make_category(name="ToRemove")
    res = client.delete(f"/categories/{cat['id']}", headers=admin_headers)
    assert res.status_code == 204
    assert client.get(f"/categories/{cat['id']}").status_code == 404


def test_delete_category_not_found(client, admin_headers):
    assert client.delete("/categories/9999", headers=admin_headers).status_code == 404
