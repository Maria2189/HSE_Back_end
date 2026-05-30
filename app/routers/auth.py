"""
Эндпоинты регистрации, входа, обновления токена и смены пароля.

Защита от SQL-инъекций обеспечивается параметризацией запросов на уровне
SQLAlchemy ORM — все значения передаются как bind-параметры, а не подставляются
строковой конкатенацией.
"""
import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.database.models import User
from app.schemas.auth import (
    UserCreate, UserResponse, Token, TokenRefreshRequest, PasswordChangeRequest,
)
from app.services import users as users_service
from app.core.security import (
    verify_password, create_access_token, create_refresh_token, decode_token,
)
from app.core.dependencies import get_current_user


router = APIRouter(prefix="/auth", tags=["Auth"])


def _issue_tokens(user: User) -> dict:
    return {
        "access_token": create_access_token({"sub": user.email, "role": user.role}),
        "refresh_token": create_refresh_token({"sub": user.email}),
        "token_type": "bearer",
    }


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
def register(user: UserCreate, db: Session = Depends(get_db)):
    """Регистрация нового пользователя с ролью `user` (роль `admin` назначается отдельно)."""
    if users_service.get_user_by_email(db, email=user.email):
        raise HTTPException(status_code=400, detail="Email already registered")

    new_user = users_service.create_user(
        db,
        email=user.email,
        password=user.password,
        first_name=user.first_name,
        last_name=user.last_name,
        role="user",
    )
    return _issue_tokens(new_user)


@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    Стандартная OAuth2-форма: поля `username` (email) и `password`.
    """
    user = users_service.get_user_by_email(db, email=form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return _issue_tokens(user)


@router.post("/refresh", response_model=Token)
def refresh_token(body: TokenRefreshRequest, db: Session = Depends(get_db)):
    """Обмен валидного refresh-токена на новую пару access+refresh."""
    try:
        payload = decode_token(body.refresh_token)
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type")
        email = payload.get("sub")
        if not email:
            raise HTTPException(status_code=401, detail="Invalid token payload")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

    user = users_service.get_user_by_email(db, email=email)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return _issue_tokens(user)


@router.post("/change-password", status_code=status.HTTP_204_NO_CONTENT)
def change_password(
    body: PasswordChangeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Смена пароля. Требует валидного access-токена и старого пароля."""
    ok = users_service.change_password(
        db, current_user, body.old_password, body.new_password
    )
    if not ok:
        raise HTTPException(status_code=400, detail="Old password is incorrect")
    return None


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """Профиль текущего пользователя."""
    return current_user
