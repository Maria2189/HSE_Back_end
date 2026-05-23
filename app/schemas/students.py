from pydantic import BaseModel
from typing import Optional

class StudentBase(BaseModel):
    first_name: str
    last_name: str
    faculty: str
    course: str
    score: int

class StudentCreate(StudentBase):
    pass

class StudentUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    faculty: Optional[str] = None
    course: Optional[str] = None
    score: Optional[int] = None

class StudentResponse(StudentBase):
    id: int

    class Config:
        from_attributes = True