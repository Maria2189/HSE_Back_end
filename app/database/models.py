from sqlalchemy import Column, Integer, String
from app.database.session import Base

class StudentRecord(Base):
    __tablename__ = 'student_records'
    
    id = Column(Integer, primary_key=True, index=True)
    last_name = Column(String, nullable=False)
    first_name = Column(String, nullable=False)
    faculty = Column(String, nullable=False)
    course = Column(String, nullable=False)
    score = Column(Integer, nullable=False)

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default="readonly", nullable=False)