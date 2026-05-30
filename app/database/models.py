"""
Модели данных платформы микрообучения.

Схема приведена к 3-й нормальной форме:
- атомарные значения (1НФ);
- неключевые поля полностью зависят от первичного ключа (2НФ);
- отсутствуют транзитивные зависимости (3НФ).

Например, имя категории хранится только в `categories`,
а не дублируется в `courses`; счётчики лайков/покупок не
кешируются в `courses`, а вычисляются агрегатами при необходимости.
"""
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Text, Boolean, ForeignKey,
    DateTime, Numeric, UniqueConstraint, Index,
)
from sqlalchemy.orm import relationship
from app.database.session import Base


class User(Base):
    """
    Пользователь платформы.

    role:
      - "user"  — обычный пользователь (может покупать курсы, ставить лайки);
      - "admin" — администратор (управляет курсами, темами, категориями).
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    role = Column(String(20), default="user", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    purchases = relationship("Purchase", back_populates="user", cascade="all, delete-orphan")
    likes = relationship("Like", back_populates="user", cascade="all, delete-orphan")


class Category(Base):
    """Категория курсов (например, «Программирование», «Дизайн»)."""
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)

    courses = relationship("Course", back_populates="category")


class Course(Base):
    """
    Курс — основная сущность каталога.

    price — стоимость в условных единицах (Numeric для точности).
    Метаинформация хранится здесь, контент тем — в таблице `topics`.
    """
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=False)
    price = Column(Numeric(10, 2), nullable=False, default=0)
    category_id = Column(
        Integer,
        ForeignKey("categories.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    author_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    category = relationship("Category", back_populates="courses")
    topics = relationship(
        "Topic",
        back_populates="course",
        cascade="all, delete-orphan",
        order_by="Topic.order",
    )
    purchases = relationship("Purchase", back_populates="course", cascade="all, delete-orphan")
    likes = relationship("Like", back_populates="course", cascade="all, delete-orphan")


class Topic(Base):
    """
    Тема курса (урок). Содержит текстовый контент.

    is_free:
      - True  — пробная тема, доступна авторизованному пользователю
                до покупки курса (по требованию задания — минимум одна).
      - False — доступна только владельцу курса или администратору.

    order — порядковый номер темы внутри курса (уникален в рамках курса).
    """
    __tablename__ = "topics"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(
        Integer,
        ForeignKey("courses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    order = Column(Integer, nullable=False, default=0)
    is_free = Column(Boolean, nullable=False, default=False)

    course = relationship("Course", back_populates="topics")

    __table_args__ = (
        UniqueConstraint("course_id", "order", name="uq_topic_course_order"),
    )


class Purchase(Base):
    """
    Факт покупки курса пользователем. Many-to-many с дополнительными
    атрибутами (дата покупки) — поэтому вынесено в самостоятельную таблицу.
    """
    __tablename__ = "purchases"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    course_id = Column(
        Integer,
        ForeignKey("courses.id", ondelete="CASCADE"),
        nullable=False,
    )
    purchased_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="purchases")
    course = relationship("Course", back_populates="purchases")

    __table_args__ = (
        UniqueConstraint("user_id", "course_id", name="uq_purchase_user_course"),
        Index("ix_purchase_user_course", "user_id", "course_id"),
    )


class Like(Base):
    """Лайк (оценка) курса от пользователя — 1 пользователь = 1 лайк на курс."""
    __tablename__ = "likes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    course_id = Column(
        Integer,
        ForeignKey("courses.id", ondelete="CASCADE"),
        nullable=False,
    )
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="likes")
    course = relationship("Course", back_populates="likes")

    __table_args__ = (
        UniqueConstraint("user_id", "course_id", name="uq_like_user_course"),
    )
