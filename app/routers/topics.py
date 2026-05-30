"""
Эндпоинты для работы с темами (уроками) курса.
Управление темами — только администратор. Чтение конкретной темы доступно
тем, кто купил курс (или администратору).
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.database.models import User
from app.schemas.topics import TopicCreate, TopicUpdate, TopicResponse
from app.services import topics as svc
from app.services import courses as courses_svc
from app.core.dependencies import admin_only, get_current_user


router = APIRouter(tags=["Topics"])


@router.get("/courses/{course_id}/topics", response_model=list[TopicResponse])
def list_topics(course_id: int, db: Session = Depends(get_db)):
    """Список тем курса (без проверки доступа к контенту — это делает /courses/{id})."""
    if not courses_svc.get_course(db, course_id):
        raise HTTPException(status_code=404, detail="Course not found")
    return svc.list_topics(db, course_id)


@router.post(
    "/courses/{course_id}/topics",
    response_model=TopicResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(admin_only)],
)
def create_topic(course_id: int, data: TopicCreate, db: Session = Depends(get_db)):
    if not courses_svc.get_course(db, course_id):
        raise HTTPException(status_code=404, detail="Course not found")
    return svc.create_topic(db, course_id, data)


@router.get("/topics/{topic_id}", response_model=TopicResponse)
def get_topic(
    topic_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Получить тему целиком. Требует доступа к курсу (покупка или admin)."""
    topic = svc.get_topic(db, topic_id)
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")

    if topic.is_free:
        return topic
    if courses_svc.has_access_to_course(
        db, current_user.id, current_user.role, topic.course_id
    ):
        return topic
    raise HTTPException(status_code=403, detail="Course not purchased")


@router.patch(
    "/topics/{topic_id}",
    response_model=TopicResponse,
    dependencies=[Depends(admin_only)],
)
def update_topic(topic_id: int, data: TopicUpdate, db: Session = Depends(get_db)):
    topic = svc.get_topic(db, topic_id)
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    return svc.update_topic(db, topic, data)


@router.delete(
    "/topics/{topic_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(admin_only)],
)
def delete_topic(topic_id: int, db: Session = Depends(get_db)):
    topic = svc.get_topic(db, topic_id)
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    svc.delete_topic(db, topic)
    return None
