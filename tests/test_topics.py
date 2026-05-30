"""Функциональные тесты эндпоинтов для тем (уроков) курса."""


def test_create_topic_admin(client, admin_headers, make_course):
    course = make_course()
    res = client.post(
        f"/courses/{course['id']}/topics",
        json={"title": "Урок 1", "content": "Содержимое", "order": 0, "is_free": True},
        headers=admin_headers,
    )
    assert res.status_code == 201
    assert res.json()["course_id"] == course["id"]


def test_create_topic_user_forbidden(client, user_headers, make_course):
    course = make_course()
    res = client.post(
        f"/courses/{course['id']}/topics",
        json={"title": "X", "content": "y", "order": 0},
        headers=user_headers,
    )
    assert res.status_code == 403


def test_create_topic_invalid_course(client, admin_headers):
    res = client.post(
        "/courses/9999/topics",
        json={"title": "X", "content": "y", "order": 0},
        headers=admin_headers,
    )
    assert res.status_code == 404


def test_create_topic_duplicate_order_in_course(client, admin_headers, make_course, make_topic):
    """В рамках курса порядок темы уникален — провал на уровне БД."""
    course = make_course()
    make_topic(course["id"], order=0)
    res = client.post(
        f"/courses/{course['id']}/topics",
        json={"title": "X", "content": "y", "order": 0},
        headers=admin_headers,
    )
    assert res.status_code in (400, 409, 500)


def test_list_topics(client, make_course, make_topic):
    course = make_course()
    make_topic(course["id"], title="B", order=1)
    make_topic(course["id"], title="A", order=0)
    res = client.get(f"/courses/{course['id']}/topics")
    assert res.status_code == 200
    titles = [t["title"] for t in res.json()]
    assert titles == ["A", "B"]


def test_list_topics_course_not_found(client):
    assert client.get("/courses/9999/topics").status_code == 404


def test_get_free_topic_no_auth_required(client, make_course, make_topic, user_headers):
    """Бесплатная тема доступна любому авторизованному."""
    course = make_course()
    topic = make_topic(course["id"], content="FREE", is_free=True, order=0)
    res = client.get(f"/topics/{topic['id']}", headers=user_headers)
    assert res.status_code == 200
    assert res.json()["content"] == "FREE"


def test_get_paid_topic_blocked_without_purchase(client, make_course, make_topic, user_headers):
    course = make_course()
    topic = make_topic(course["id"], content="PAID", is_free=False, order=0)
    res = client.get(f"/topics/{topic['id']}", headers=user_headers)
    assert res.status_code == 403


def test_get_paid_topic_after_purchase(client, make_course, make_topic, user_headers):
    course = make_course()
    topic = make_topic(course["id"], content="PAID", is_free=False, order=0)
    client.post(f"/courses/{course['id']}/purchase", headers=user_headers)
    res = client.get(f"/topics/{topic['id']}", headers=user_headers)
    assert res.status_code == 200
    assert res.json()["content"] == "PAID"


def test_get_paid_topic_as_admin(client, make_course, make_topic, admin_headers):
    course = make_course()
    topic = make_topic(course["id"], content="PAID", is_free=False, order=0)
    res = client.get(f"/topics/{topic['id']}", headers=admin_headers)
    assert res.status_code == 200


def test_update_topic_admin(client, admin_headers, make_course, make_topic):
    course = make_course()
    topic = make_topic(course["id"], order=0)
    res = client.patch(
        f"/topics/{topic['id']}",
        json={"title": "Обновлено"},
        headers=admin_headers,
    )
    assert res.status_code == 200
    assert res.json()["title"] == "Обновлено"


def test_update_topic_user_forbidden(client, user_headers, make_course, make_topic):
    course = make_course()
    topic = make_topic(course["id"], order=0)
    res = client.patch(
        f"/topics/{topic['id']}",
        json={"title": "Hack"},
        headers=user_headers,
    )
    assert res.status_code == 403


def test_delete_topic(client, admin_headers, make_course, make_topic):
    course = make_course()
    topic = make_topic(course["id"], order=0)
    res = client.delete(f"/topics/{topic['id']}", headers=admin_headers)
    assert res.status_code == 204


def test_delete_topic_not_found(client, admin_headers):
    assert client.delete("/topics/9999", headers=admin_headers).status_code == 404
