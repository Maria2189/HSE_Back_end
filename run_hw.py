from app.database.session import engine, SessionLocal, Base
from app.database.models import StudentRecord
from app.database.crud import student_crud

Base.metadata.create_all(bind=engine)

db = SessionLocal()

try:
    print("Загрузка данных из CSV...")
    #student_crud.load_from_csv(db, "students.csv")
    print("Данные готовы!\n")

    print("--- Уникальные курсы ---")
    print(student_crud.get_unique_courses(db))

    print("\n--- Студенты факультета РЭФ ---")
    for student in student_crud.get_students_by_faculty(db, "РЭФ"):
        print(f"{student.last_name} {student.first_name} | Оценка: {student.score}")

    print("\n--- Студенты с баллом ниже 30 по курсу 'Мат. Анализ' ---")
    for student in student_crud.get_students_with_low_score(db, "Мат. Анализ", 30):
        print(f"{student.last_name} {student.first_name} | Оценка: {student.score}")

    print("\n--- Средний балл факультета РЭФ ---")
    print(student_crud.get_average_score_by_faculty(db, "РЭФ"))

finally:
    db.close()