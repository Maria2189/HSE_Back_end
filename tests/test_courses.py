"""Функциональные тесты эндпоинтов /courses (каталог, доступ, лайки, покупка)."""
from decimal import Decimal


# ---------- Каталог и CRUD ----------

def test_catalog_public(client):
    """Каталог доступен без авторизации."""
    res = client.get("/courses/")
    assert res.status_code == 200
    assert res.json() == []


def test_create_course_admin(client, admin_headers, make_category):
    cat = make_category()
    res = client.post(
        "/courses/",
        json={
            "title": "Python с нуля",
            "description": "Курс для начинающих",
            "price": "100.00",
            "category_id": cat["id"],
        },
        headers=admin_headers,
    )
    assert res.status_code == 201
    assert res.json()["title"] == "Python с нуля"


def test_create_course_user_forbidden(client, user_headers, make_category):
    cat = make_category()
    res = client.post(
        "/courses/",
        json={
            "title": "Hack",
            "description": "x",
            "price": "0",
            "category_id": cat["id"],
        },
        headers=user_headers,
    )
    assert res.status_code == 403


def test_create_course_requires_auth(client, make_category):
    cat = make_category()
    res = client.post(
        "/courses/",
        json={
            "title": "X",
            "description": "y",
            "price": "0",
            "category_id": cat["id"],
        },
    )
    assert res.status_code == 401


def test_create_course_invalid_category(client, admin_headers):
    res = client.post(
        "/courses/",
        json={
            "title": "X",
            "description": "y",
            "price": "10",
            "category_id": 9999,
        },
        headers=admin_headers,
    )
    assert res.status_code == 400


def test_create_course_negative_price(client, admin_headers, make_category):
    cat = make_category()
    res = client.post(
        "/courses/",
        json={
            "title": "X",
            "description": "y",
            "price": "-5",
            "category_id": cat["id"],
        },
        headers=admin_headers,
    )
    assert res.status_code == 422


def test_list_courses_after_create(client, make_course):
    make_course(title="Курс 1")
    make_course(title="Курс 2")
    res = client.get("/courses/")
    assert res.status_code == 200
    titles = [c["title"] for c in res.json()]
    assert "Курс 1" in titles and "Курс 2" in titles


def test_list_courses_filter_by_category(client, admin_headers, make_category):
    """Фильтрация каталога по category_id."""
    cat1 = make_category(name="Кат1")
    cat2 = make_category(name="Кат2")

    for title, cid in [("A", cat1["id"]), ("B", cat1["id"]), ("C", cat2["id"])]:
        client.post(
            "/courses/",
            json={"title": title, "description": "d", "price": "0", "category_id": cid},
            headers=admin_headers,
        )

    res = client.get(f"/courses/?category_id={cat1['id']}")
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 2
    assert all(c["category"]["id"] == cat1["id"] for c in data)


def test_list_courses_pagination(client, admin_headers, make_category):
    cat = make_category()
    for i in range(5):
        client.post(
            "/courses/",
            json={"title": f"C{i}", "description": "d", "price": "0", "category_id": cat["id"]},
            headers=admin_headers,
        )
    res = client.get("/courses/?skip=2&limit=2")
    assert res.status_code == 200
    assert len(res.json()) == 2


def test_update_course(client, admin_headers, make_course):
    course = make_course(title="Старое")
    res = client.patch(
        f"/courses/{course['id']}",
        json={"title": "Новое", "price": "500"},
        headers=admin_headers,
    )
    assert res.status_code == 200


def test_update_course_user_forbidden(client, user_headers, make_course):
    course = make_course()
    res = client.patch(
        f"/courses/{course['id']}",
        json={"title": "Hack"},
        headers=user_headers,
    )
    assert res.status_code == 403


def test_delete_course(client, admin_headers, make_course):
    course = make_course()
    assert client.delete(f"/courses/{course['id']}", headers=admin_headers).status_code == 204
    assert client.get(f"/courses/{course['id']}").status_code == 404


def test_get_course_not_found(client):
    assert client.get("/courses/9999").status_code == 404


# ---------- Страница курса и доступ к темам ----------

def test_course_page_anonymous_sees_only_free(client, make_course, make_topic):
    """Анонимный пользователь видит контент только бесплатной темы."""
    course = make_course()
    make_topic(course["id"], title="Вводная", content="FREE!", order=0, is_free=True)
    make_topic(course["id"], title="Платная", content="PAID!", order=1, is_free=False)

    res = client.get(f"/courses/{course['id']}")
    assert res.status_code == 200
    page = res.json()
    assert page["is_purchased"] is False

    topics = {t["order"]: t for t in page["topics"]}
    assert topics[0]["content"] == "FREE!"
    assert topics[0]["locked"] is False
    assert topics[1]["content"] == ""
    assert topics[1]["locked"] is True


def test_course_page_authenticated_not_purchased(client, make_course, make_topic, user_headers):
    """Авторизованный пользователь без покупки тоже видит только free."""
    course = make_course()
    make_topic(course["id"], content="FREE", is_free=True, order=0)
    make_topic(course["id"], content="PAID", is_free=False, order=1)

    res = client.get(f"/courses/{course['id']}", headers=user_headers)
    assert res.status_code == 200
    page = res.json()
    assert page["is_purchased"] is False
    paid = next(t for t in page["topics"] if t["order"] == 1)
    assert paid["locked"] is True and paid["content"] == ""


def test_course_page_after_purchase_unlocks_all(client, make_course, make_topic, user_headers):
    """После покупки пользователь видит контент всех тем."""
    course = make_course(price="50")
    make_topic(course["id"], content="FREE", is_free=True, order=0)
    make_topic(course["id"], content="PAID-CONTENT", is_free=False, order=1)

    buy = client.post(f"/courses/{course['id']}/purchase", headers=user_headers)
    assert buy.status_code == 201

    res = client.get(f"/courses/{course['id']}", headers=user_headers)
    page = res.json()
    assert page["is_purchased"] is True
    for t in page["topics"]:
        assert t["locked"] is False
    paid = next(t for t in page["topics"] if t["order"] == 1)
    assert paid["content"] == "PAID-CONTENT"


def test_course_page_admin_sees_all(client, make_course, make_topic, admin_headers):
    course = make_course()
    make_topic(course["id"], content="PAID", is_free=False, order=0)
    res = client.get(f"/courses/{course['id']}", headers=admin_headers)
    page = res.json()
    assert page["topics"][0]["content"] == "PAID"
    assert page["topics"][0]["locked"] is False


# ---------- Покупка ----------

def test_purchase_course_success(client, make_course, user_headers):
    course = make_course()
    res = client.post(f"/courses/{course['id']}/purchase", headers=user_headers)
    assert res.status_code == 201
    assert res.json()["status"] == "purchased"


def test_purchase_course_requires_auth(client, make_course):
    course = make_course()
    res = client.post(f"/courses/{course['id']}/purchase")
    assert res.status_code == 401


def test_purchase_course_twice_conflict(client, make_course, user_headers):
    course = make_course()
    client.post(f"/courses/{course['id']}/purchase", headers=user_headers)
    res = client.post(f"/courses/{course['id']}/purchase", headers=user_headers)
    assert res.status_code == 409


def test_purchase_nonexistent_course(client, user_headers):
    res = client.post("/courses/9999/purchase", headers=user_headers)
    assert res.status_code == 404


# ---------- Лайки ----------

def test_like_course(client, make_course, user_headers):
    course = make_course()
    res = client.post(f"/courses/{course['id']}/like", headers=user_headers)
    assert res.status_code == 204

    stats = client.get(f"/courses/{course['id']}/stats").json()
    assert stats["likes_count"] == 1


def test_like_idempotent(client, make_course, user_headers):
    """Двойной POST /like не должен ронять и не должен удваивать лайк."""
    course = make_course()
    client.post(f"/courses/{course['id']}/like", headers=user_headers)
    client.post(f"/courses/{course['id']}/like", headers=user_headers)
    stats = client.get(f"/courses/{course['id']}/stats").json()
    assert stats["likes_count"] == 1


def test_unlike(client, make_course, user_headers):
    course = make_course()
    client.post(f"/courses/{course['id']}/like", headers=user_headers)
    res = client.delete(f"/courses/{course['id']}/like", headers=user_headers)
    assert res.status_code == 204
    stats = client.get(f"/courses/{course['id']}/stats").json()
    assert stats["likes_count"] == 0


def test_like_requires_auth(client, make_course):
    course = make_course()
    assert client.post(f"/courses/{course['id']}/like").status_code == 401


def test_like_nonexistent_course(client, user_headers):
    res = client.post("/courses/9999/like", headers=user_headers)
    assert res.status_code == 404


# ---------- Статистика ----------

def test_stats_counts(client, make_course, user_headers, second_user_headers):
    """Лайки и студенты считаются независимо для разных пользователей."""
    course = make_course()
    client.post(f"/courses/{course['id']}/like", headers=user_headers)
    client.post(f"/courses/{course['id']}/like", headers=second_user_headers)
    client.post(f"/courses/{course['id']}/purchase", headers=user_headers)

    stats = client.get(f"/courses/{course['id']}/stats").json()
    assert stats["likes_count"] == 2
    assert stats["students_count"] == 1


def test_stats_not_found(client):
    assert client.get("/courses/9999/stats").status_code == 404


# ---------- /me/courses ----------

def test_me_courses_lists_only_purchased(client, make_course, user_headers, second_user_headers):
    c1 = make_course(title="Купленный")
    c2 = make_course(title="Не купленный")
    client.post(f"/courses/{c1['id']}/purchase", headers=user_headers)
    # Второй пользователь покупает c2 — не должен влиять на user_headers
    client.post(f"/courses/{c2['id']}/purchase", headers=second_user_headers)

    res = client.get("/me/courses", headers=user_headers)
    assert res.status_code == 200
    titles = [c["title"] for c in res.json()]
    assert titles == ["Купленный"]


def test_me_courses_requires_auth(client):
    assert client.get("/me/courses").status_code == 401
