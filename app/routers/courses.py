"""
Эндпоинты для каталога курсов, отдельной страницы курса,
а также действий — лайки, покупка, статистика.
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from fastapi_cache.decorator import cache

from app.database.session import get_db
from app.database.models import User
from app.schemas.courses import (
    CourseCreate, CourseUpdate, CourseResponse,
    CourseListItem, CoursePage, CourseStats,
)
from app.schemas.topics import TopicPreview
from app.services import courses as svc
from app.services import categories as cat_svc
from app.core.dependencies import admin_only, authenticated_only, get_optional_user


router = APIRouter(prefix="/courses", tags=["Courses"])


def _build_list_item(db: Session, course) -> CourseListItem:
    return CourseListItem(
        id=course.id,
        title=course.title,
        description=course.description,
        price=course.price,
        category=course.category,
        likes_count=svc.get_likes_count(db, course.id),
        students_count=svc.get_students_count(db, course.id),
    )


# ---------- Каталог ----------

@router.get("/", response_model=list[CourseListItem])
def list_courses(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    category_id: int | None = Query(None, gt=0, description="Фильтр по категории"),
    db: Session = Depends(get_db),
):
    """Каталог курсов с пагинацией и опциональным фильтром по категории."""
    courses = svc.list_courses(db, skip=skip, limit=limit, category_id=category_id)
    return [_build_list_item(db, c) for c in courses]


# ---------- Страница курса с учётом прав доступа ----------

@router.get("/{course_id}", response_model=CoursePage)
def get_course_page(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_optional_user),
):
    """
    Возвращает метаинформацию + темы. Контент тем:
      - анонимные/неоплатившие пользователи видят полный контент только у `is_free=True`;
      - администраторы и купившие курс видят все темы целиком.
    """
    course = svc.get_course(db, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    user_id = current_user.id if current_user else None
    role = current_user.role if current_user else None
    has_full_access = svc.has_access_to_course(db, user_id, role, course_id)

    is_purchased = (
        current_user is not None
        and svc.get_purchase(db, current_user.id, course_id) is not None
    )

    topic_previews: list[TopicPreview] = []
    for t in course.topics:
        unlocked = has_full_access or t.is_free
        topic_previews.append(TopicPreview(
            id=t.id,
            title=t.title,
            order=t.order,
            is_free=t.is_free,
            locked=not unlocked,
            content=t.content if unlocked else "",
        ))

    return CoursePage(
        id=course.id,
        title=course.title,
        description=course.description,
        price=course.price,
        category=course.category,
        likes_count=svc.get_likes_count(db, course.id),
        students_count=svc.get_students_count(db, course.id),
        is_purchased=is_purchased,
        topics=topic_previews,
    )


# ---------- Управление курсами (admin) ----------

@router.post("/", response_model=CourseResponse, status_code=status.HTTP_201_CREATED)
def create_course(
    data: CourseCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(admin_only),
):
    if not cat_svc.get_category(db, data.category_id):
        raise HTTPException(status_code=400, detail="Category does not exist")
    return svc.create_course(db, data, author_id=admin.id)


@router.patch("/{course_id}", response_model=CourseResponse, dependencies=[Depends(admin_only)])
def update_course(course_id: int, data: CourseUpdate, db: Session = Depends(get_db)):
    course = svc.get_course(db, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    if data.category_id is not None and not cat_svc.get_category(db, data.category_id):
        raise HTTPException(status_code=400, detail="Category does not exist")
    return svc.update_course(db, course, data)


@router.delete(
    "/{course_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(admin_only)],
)
def delete_course(course_id: int, db: Session = Depends(get_db)):
    course = svc.get_course(db, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    svc.delete_course(db, course)
    return None


# ---------- Лайки ----------

@router.post("/{course_id}/like", status_code=status.HTTP_204_NO_CONTENT)
def like_course(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(authenticated_only),
):
    """Идемпотентный лайк: повторный POST не возвращает ошибку."""
    if not svc.get_course(db, course_id):
        raise HTTPException(status_code=404, detail="Course not found")
    svc.add_like(db, current_user.id, course_id)
    return None


@router.delete("/{course_id}/like", status_code=status.HTTP_204_NO_CONTENT)
def unlike_course(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(authenticated_only),
):
    if not svc.get_course(db, course_id):
        raise HTTPException(status_code=404, detail="Course not found")
    svc.remove_like(db, current_user.id, course_id)
    return None


# ---------- Покупка ----------

@router.post("/{course_id}/purchase", status_code=status.HTTP_201_CREATED)
def buy_course(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(authenticated_only),
):
    """
    Покупка курса. В реальном проекте здесь была бы интеграция с платежами;
    в учебном — мы просто фиксируем факт покупки.
    """
    if not svc.get_course(db, course_id):
        raise HTTPException(status_code=404, detail="Course not found")
    purchase = svc.purchase_course(db, current_user.id, course_id)
    if purchase is None:
        raise HTTPException(status_code=409, detail="Course already purchased")
    return {"course_id": course_id, "user_id": current_user.id, "status": "purchased"}


# ---------- Статистика ----------

@router.get("/{course_id}/stats", response_model=CourseStats)
@cache(expire=30)
def course_stats(course_id: int, db: Session = Depends(get_db)):
    """Публичная статистика — лайки и количество студентов. Кешируется на 30 с."""
    if not svc.get_course(db, course_id):
        raise HTTPException(status_code=404, detail="Course not found")
    return CourseStats(
        course_id=course_id,
        likes_count=svc.get_likes_count(db, course_id),
        students_count=svc.get_students_count(db, course_id),
    )
