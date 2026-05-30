"""Pydantic-схемы для курсов и связанной статистики."""
from typing import Optional, List
from decimal import Decimal
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

from app.schemas.topics import TopicPreview
from app.schemas.categories import CategoryResponse


class CourseBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., min_length=1)
    price: Decimal = Field(..., ge=0, decimal_places=2)
    category_id: int = Field(..., gt=0)


class CourseCreate(CourseBase):
    pass


class CourseUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, min_length=1)
    price: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    category_id: Optional[int] = Field(None, gt=0)


class CourseResponse(CourseBase):
    """Краткий ответ для списков."""
    id: int
    author_id: Optional[int]
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class CourseListItem(BaseModel):
    """Элемент каталога: курс + категория + статистика."""
    id: int
    title: str
    description: str
    price: Decimal
    category: CategoryResponse
    likes_count: int
    students_count: int
    model_config = ConfigDict(from_attributes=True)


class CoursePage(BaseModel):
    """
    Страница курса — то, что видит студент:
    метаинформация + список тем (с разделением на платные/бесплатные).
    """
    id: int
    title: str
    description: str
    price: Decimal
    category: CategoryResponse
    likes_count: int
    students_count: int
    is_purchased: bool = Field(..., description="Купил ли текущий пользователь курс")
    topics: List[TopicPreview]
    model_config = ConfigDict(from_attributes=True)


class CourseStats(BaseModel):
    course_id: int
    likes_count: int
    students_count: int
