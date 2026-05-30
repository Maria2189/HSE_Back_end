"""Сервисный слой для работы с категориями курсов."""
from sqlalchemy.orm import Session
from app.database.models import Category
from app.schemas.categories import CategoryCreate, CategoryUpdate


def list_categories(db: Session, skip: int = 0, limit: int = 100) -> list[Category]:
    return db.query(Category).order_by(Category.id).offset(skip).limit(limit).all()


def get_category(db: Session, category_id: int) -> Category | None:
    return db.query(Category).filter(Category.id == category_id).first()


def get_category_by_name(db: Session, name: str) -> Category | None:
    return db.query(Category).filter(Category.name == name).first()


def create_category(db: Session, data: CategoryCreate) -> Category:
    db_category = Category(**data.model_dump())
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category


def update_category(db: Session, category: Category, data: CategoryUpdate) -> Category:
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(category, field, value)
    db.commit()
    db.refresh(category)
    return category


def delete_category(db: Session, category: Category) -> None:
    db.delete(category)
    db.commit()
