from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
from fastapi_cache.decorator import cache

from app.database.session import SessionLocal
from app.database.crud import student_crud 
from app.schemas.students import StudentCreate, StudentUpdate, StudentResponse, BulkDeleteRequest
from app.core.dependencies import get_current_user_token_data, RoleChecker

router = APIRouter(
    prefix="/students",
    tags=["Students"]
)

allow_read = RoleChecker(["readonly", "student", "admin"])
allow_write = RoleChecker(["student", "admin"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/", response_model=StudentResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(allow_write)])
def create_student(student: StudentCreate, db: Session = Depends(get_db)):
    return student_crud.create_student(db, student)

@router.get("/{student_id}", response_model=StudentResponse, dependencies=[Depends(allow_read)])
@cache(expire=60)  # Шаг 3: Кеширование ответа эндпоинта в Redis на 60 секунд
def read_student(student_id: int, db: Session = Depends(get_db)):
    db_student = student_crud.get_student_by_id(db, student_id)
    if db_student is None:
        raise HTTPException(status_code=404, detail="Student not found")
    return db_student

@router.patch("/{student_id}", response_model=StudentResponse, dependencies=[Depends(allow_write)])
def update_student(student_id: int, student: StudentUpdate, db: Session = Depends(get_db)):
    db_student = student_crud.update_student(db, student_id, student)
    if db_student is None:
        raise HTTPException(status_code=404, detail="Student not found")
    return db_student

@router.delete("/{student_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(allow_write)])
def delete_student(student_id: int, db: Session = Depends(get_db)):
    db_student = student_crud.delete_student(db, student_id)
    if db_student is None:
        raise HTTPException(status_code=404, detail="Student not found")
    return None



@router.post("/load-csv", status_code=status.HTTP_202_ACCEPTED, dependencies=[Depends(allow_write)])
def load_csv_background(file_path: str, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Фоновое наполнение базы данных из указанного CSV-файла"""
    background_tasks.add_task(student_crud.load_from_csv, db, file_path)
    return {"message": "Загрузка данных из CSV запущена в фоновом режиме"}

@router.post("/bulk-delete", status_code=status.HTTP_202_ACCEPTED, dependencies=[Depends(allow_write)])
def bulk_delete_background(request: BulkDeleteRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Фоновое удаление записей из базы данных по переданному списку ID"""
    background_tasks.add_task(student_crud.delete_students_bulk, db, request.student_ids)
    return {"message": "Удаление записей запущено в фоновом режиме"}