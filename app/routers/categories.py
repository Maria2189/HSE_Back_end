"""Эндпоинты для работы с категориями курсов."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from fastapi_cache.decorator import cache

from app.database.session import get_db
from app.schemas.categories import CategoryCreate, CategoryUpdate, CategoryResponse
from app.services import categories as svc
from app.core.dependencies import admin_only


router = APIRouter(prefix="/categories", tags=["Categories"])


@router.get("/", response_model=list[CategoryResponse])
@cache(expire=60)
def list_categories(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Публичный список категорий с пагинацией. Кешируется в Redis на 60 с."""
    return svc.list_categories(db, skip=skip, limit=limit)


@router.get("/{category_id}", response_model=CategoryResponse)
def get_category(category_id: int, db: Session = Depends(get_db)):
    cat = svc.get_category(db, category_id)
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")
    return cat


@router.post(
    "/",
    response_model=CategoryResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(admin_only)],
)
def create_category(data: CategoryCreate, db: Session = Depends(get_db)):
    if svc.get_category_by_name(db, data.name):
        raise HTTPException(status_code=400, detail="Category with this name already exists")
    return svc.create_category(db, data)


@router.patch(
    "/{category_id}",
    response_model=CategoryResponse,
    dependencies=[Depends(admin_only)],
)
def update_category(category_id: int, data: CategoryUpdate, db: Session = Depends(get_db)):
    cat = svc.get_category(db, category_id)
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")
    return svc.update_category(db, cat, data)


@router.delete(
    "/{category_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(admin_only)],
)
def delete_category(category_id: int, db: Session = Depends(get_db)):
    cat = svc.get_category(db, category_id)
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")
    svc.delete_category(db, cat)
    return None
