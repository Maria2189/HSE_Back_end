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