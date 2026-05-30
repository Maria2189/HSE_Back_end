"""Pydantic-схемы для тем (уроков) курса."""
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class TopicBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    content: str = Field(..., min_length=1)
    order: int = Field(..., ge=0, description="Порядковый номер темы внутри курса")
    is_free: bool = Field(False, description="Пробная тема, доступна до покупки")


class TopicCreate(TopicBase):
    pass


class TopicUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    content: Optional[str] = Field(None, min_length=1)
    order: Optional[int] = Field(None, ge=0)
    is_free: Optional[bool] = None


class TopicResponse(TopicBase):
    id: int
    course_id: int
    model_config = ConfigDict(from_attributes=True)


class TopicPreview(BaseModel):
    """
    Превью темы для эндпоинта страницы курса:
    если у пользователя нет доступа — поле content будет пустой строкой
    и locked=True.
    """
    id: int
    title: str
    order: int
    is_free: bool
    locked: bool = Field(..., description="True, если контент скрыт")
    content: str = Field("", description="Текст темы, либо пустая строка")
    model_config = ConfigDict(from_attributes=True)
