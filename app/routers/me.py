"""Личный кабинет пользователя."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.database.models import User
from app.schemas.courses import CourseListItem
from app.services import courses as svc
from app.core.dependencies import get_current_user


router = APIRouter(prefix="/me", tags=["Me"])


@router.get("/courses", response_model=list[CourseListItem])
def my_courses(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Курсы, купленные текущим пользователем."""
    courses = svc.list_user_purchases(db, current_user.id)
    return [
        CourseListItem(
            id=c.id,
            title=c.title,
            description=c.description,
            price=c.price,
            category=c.category,
            likes_count=svc.get_likes_count(db, c.id),
            students_count=svc.get_students_count(db, c.id),
        )
        for c in courses
    ]
