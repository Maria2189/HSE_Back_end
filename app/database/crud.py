import csv
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database.models import StudentRecord

class StudentCRUD:
    """
    Класс для выполнения операций INSERT и SELECT для модели StudentRecord
    """

    def load_from_csv(self, db: Session, file_path: str):
        """
        Метод для заполнения модели данными из файла students.csv
        """
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
        """
        Получение списка студентов по названию факультета
        """
        return db.query(StudentRecord).filter(StudentRecord.faculty == faculty_name).all()

    def get_unique_courses(self, db: Session) -> list[str]:
        """
        Получение списка уникальных курсов
        """
        courses = db.query(StudentRecord.course).distinct().all()
        return [course[0] for course in courses]

    def get_students_with_low_score(self, db: Session, course_name: str, threshold: int = 30):
        """
        Получение студентов по выбранному курсу с оценкой ниже 30 баллов
        """
        return db.query(StudentRecord).filter(
            StudentRecord.course == course_name,
            StudentRecord.score < threshold
        ).all()

    def get_average_score_by_faculty(self, db: Session, faculty_name: str) -> float:
        """
        Получение среднего балла по факультету
        """
        avg_score = db.query(func.avg(StudentRecord.score)).filter(
            StudentRecord.faculty == faculty_name
        ).scalar()
        
        return round(float(avg_score), 2) if avg_score else 0.0

student_crud = StudentCRUD()