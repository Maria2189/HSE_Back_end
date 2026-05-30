"""Сервисный слой для работы с курсами, лайками и покупками."""
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.database.models import Course, Like, Purchase, Topic
from app.schemas.courses import CourseCreate, CourseUpdate


# ---------- Каталог курсов ----------

def list_courses(
    db: Session,
    skip: int = 0,
    limit: int = 20,
    category_id: int | None = None,
) -> list[Course]:
    """Возвращает курсы с подгруженной категорией. Поддерживает фильтр по категории."""
    q = db.query(Course).options(joinedload(Course.category))
    if category_id is not None:
        q = q.filter(Course.category_id == category_id)
    return q.order_by(Course.id).offset(skip).limit(limit).all()


def get_course(db: Session, course_id: int) -> Course | None:
    return (
        db.query(Course)
        .options(joinedload(Course.category), joinedload(Course.topics))
        .filter(Course.id == course_id)
        .first()
    )


def create_course(db: Session, data: CourseCreate, author_id: int) -> Course:
    db_course = Course(**data.model_dump(), author_id=author_id)
    db.add(db_course)
    db.commit()
    db.refresh(db_course)
    return db_course


def update_course(db: Session, course: Course, data: CourseUpdate) -> Course:
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(course, field, value)
    db.commit()
    db.refresh(course)
    return course


def delete_course(db: Session, course: Course) -> None:
    db.delete(course)
    db.commit()


# ---------- Статистика курсов ----------

def get_likes_count(db: Session, course_id: int) -> int:
    return db.query(func.count(Like.id)).filter(Like.course_id == course_id).scalar() or 0


def get_students_count(db: Session, course_id: int) -> int:
    return db.query(func.count(Purchase.id)).filter(Purchase.course_id == course_id).scalar() or 0


# ---------- Лайки ----------

def get_like(db: Session, user_id: int, course_id: int) -> Like | None:
    return (
        db.query(Like)
        .filter(Like.user_id == user_id, Like.course_id == course_id)
        .first()
    )


def add_like(db: Session, user_id: int, course_id: int) -> Like | None:
    """
    Добавляет лайк. Возвращает None, если пользователь уже лайкнул курс
    (вызывающая сторона трактует это как «не изменилось»).
    """
    if get_like(db, user_id, course_id) is not None:
        return None
    like = Like(user_id=user_id, course_id=course_id)
    db.add(like)
    db.commit()
    db.refresh(like)
    return like


def remove_like(db: Session, user_id: int, course_id: int) -> bool:
    like = get_like(db, user_id, course_id)
    if not like:
        return False
    db.delete(like)
    db.commit()
    return True


# ---------- Покупки ----------

def get_purchase(db: Session, user_id: int, course_id: int) -> Purchase | None:
    return (
        db.query(Purchase)
        .filter(Purchase.user_id == user_id, Purchase.course_id == course_id)
        .first()
    )


def purchase_course(db: Session, user_id: int, course_id: int) -> Purchase | None:
    """
    Создаёт запись о покупке. Если уже куплено — возвращает None
    (роутер интерпретирует как 409 Conflict).
    """
    if get_purchase(db, user_id, course_id) is not None:
        return None
    purchase = Purchase(user_id=user_id, course_id=course_id)
    db.add(purchase)
    db.commit()
    db.refresh(purchase)
    return purchase


def list_user_purchases(db: Session, user_id: int) -> list[Course]:
    """Курсы, купленные пользователем (с категорией для отображения)."""
    return (
        db.query(Course)
        .join(Purchase, Purchase.course_id == Course.id)
        .options(joinedload(Course.category))
        .filter(Purchase.user_id == user_id)
        .order_by(Purchase.purchased_at.desc())
        .all()
    )


# ---------- Доступ к контенту ----------

def has_access_to_course(db: Session, user_id: int | None, role: str | None, course_id: int) -> bool:
    """
    Полный доступ к контенту имеют:
      - администраторы;
      - пользователи, купившие курс.
    """
    if role == "admin":
        return True
    if user_id is None:
        return False
    return get_purchase(db, user_id, course_id) is not None
