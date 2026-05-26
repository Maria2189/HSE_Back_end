import csv
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database.models import StudentRecord, User
from app.database import models
from app.schemas.students import StudentCreate, StudentUpdate
from app.core.security import get_password_hash

def get_user_by_email(db: Session, email: str):
    """Поиск пользователя по email"""
    return db.query(User).filter(User.email == email).first()

def create_user(db: Session, email: str, password: str, role: str = "readonly"):
    """Создание нового пользователя с хешированием пароля"""
    hashed_password = get_password_hash(password)
    db_user = User(email=email, hashed_password=hashed_password, role=role)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

class StudentCRUD:
    """
    Класс для выполнения операций INSERT и SELECT для модели StudentRecord
    """

    def load_from_csv(self, db: Session, file_path: str):
        with open(file_path, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file) 
            
            for row in reader:
                student = StudentRecord(
                    last_name=row['Фамилия'].strip(),
                    first_name=row['Имя'].strip(),
                    faculty=row['Факультет'].strip(),
                    course=row['Курс'].strip(),
                    score=int(row['Оценка'].strip())
                )
                db.add(student)
                
        db.commit()

    def get_students_by_faculty(self, db: Session, faculty_name: str):
        return db.query(StudentRecord).filter(StudentRecord.faculty == faculty_name).all()

    def get_unique_courses(self, db: Session) -> list[str]:
        courses = db.query(StudentRecord.course).distinct().all()
        return [course[0] for course in courses]

    def get_students_with_low_score(self, db: Session, course_name: str, threshold: int = 30):
        return db.query(StudentRecord).filter(
            StudentRecord.course == course_name,
            StudentRecord.score < threshold
        ).all()

    def get_average_score_by_faculty(self, db: Session, faculty_name: str) -> float:
        avg_score = db.query(func.avg(StudentRecord.score)).filter(
            StudentRecord.faculty == faculty_name
        ).scalar()
        
        return round(float(avg_score), 2) if avg_score else 0.0
    
    def get_student_by_id(self, db: Session, student_id: int):
        return db.query(models.StudentRecord).filter(models.StudentRecord.id == student_id).first()

    def create_student(self, db: Session, student_data: StudentCreate):
        db_student = models.StudentRecord(**student_data.model_dump())
        db.add(db_student)
        db.commit()
        db.refresh(db_student)
        return db_student

    def update_student(self, db: Session, student_id: int, student_data: StudentUpdate):
        db_student = self.get_student_by_id(db, student_id)
        if db_student:
            update_data = student_data.model_dump(exclude_unset=True)
            for key, value in update_data.items():
                setattr(db_student, key, value)
            db.commit()
            db.refresh(db_student)
        return db_student

    def delete_student(self, db: Session, student_id: int):
        db_student = self.get_student_by_id(db, student_id)
        if db_student:
            db.delete(db_student)
            db.commit()
        return db_student
    
    def delete_students_bulk(self, db: Session, student_ids: list[int]):
        """Удаление записей по списку ID"""
        db.query(models.StudentRecord).filter(models.StudentRecord.id.in_(student_ids)).delete(synchronize_session=False)
        db.commit()

student_crud = StudentCRUD()