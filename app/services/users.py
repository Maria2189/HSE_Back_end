"""Сервисный слой для работы с пользователями."""
from sqlalchemy.orm import Session
from app.database.models import User
from app.core.security import get_password_hash, verify_password


def get_user_by_email(db: Session, email: str) -> User | None:
    """Поиск пользователя по email (email уникален и проиндексирован)."""
    return db.query(User).filter(User.email == email).first()


def get_user_by_id(db: Session, user_id: int) -> User | None:
    return db.query(User).filter(User.id == user_id).first()


def create_user(
    db: Session,
    email: str,
    password: str,
    first_name: str,
    last_name: str,
    role: str = "user",
) -> User:
    """Создаёт нового пользователя с захешированным паролем."""
    db_user = User(
        email=email,
        hashed_password=get_password_hash(password),
        first_name=first_name,
        last_name=last_name,
        role=role,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def change_password(db: Session, user: User, old_password: str, new_password: str) -> bool:
    """Проверяет старый пароль и устанавливает новый. Возвращает True при успехе."""
    if not verify_password(old_password, user.hashed_password):
        return False
    user.hashed_password = get_password_hash(new_password)
    db.commit()
    return True
