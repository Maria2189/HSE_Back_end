import re
from enum import Enum
from typing import List
from datetime import date, datetime
from pydantic import BaseModel, EmailStr, Field, field_validator

class AppealReason(str, Enum):
    no_network = "нет доступа к сети"
    phone_broken = "не работает телефон"
    no_emails = "не приходят письма"

class AppealCreate(BaseModel):
    surname: str
    name: str
    dob: date
    phone: str = Field(..., description="Номер телефона в международном или локальном формате")
    email: EmailStr
    reasons: List[AppealReason] 
    problem_discovery_time: datetime

    @field_validator("surname", "name")
    @classmethod
    def validate_russian_names(cls, value: str) -> str:
        if not re.match(r"^[А-ЯЁ][а-яё]+$", value):
            raise ValueError(
                "Значение должно начинаться с заглавной буквы, "
                "содержать только кириллицу и не иметь цифр или спецсимволов."
            )
        return value

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str) -> str:
        if not re.match(r"^\+?[0-9]{10,15}$", value):
            raise ValueError("Некорректный формат номера телефона. Используйте формат, например: +79991234567")
        return value