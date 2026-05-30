"""Сервисный слой для работы с темами (уроками) курса."""
from sqlalchemy.orm import Session
from app.database.models import Topic
from app.schemas.topics import TopicCreate, TopicUpdate


def list_topics(db: Session, course_id: int) -> list[Topic]:
    return (
        db.query(Topic)
        .filter(Topic.course_id == course_id)
        .order_by(Topic.order)
        .all()
    )


def get_topic(db: Session, topic_id: int) -> Topic | None:
    return db.query(Topic).filter(Topic.id == topic_id).first()


def create_topic(db: Session, course_id: int, data: TopicCreate) -> Topic:
    db_topic = Topic(course_id=course_id, **data.model_dump())
    db.add(db_topic)
    db.commit()
    db.refresh(db_topic)
    return db_topic


def update_topic(db: Session, topic: Topic, data: TopicUpdate) -> Topic:
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(topic, field, value)
    db.commit()
    db.refresh(topic)
    return topic


def delete_topic(db: Session, topic: Topic) -> None:
    db.delete(topic)
    db.commit()
