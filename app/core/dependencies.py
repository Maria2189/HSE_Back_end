"""
FastAPI-зависимости для аутентификации и проверки ролей (RBAC).

get_current_user      — обязательная аутентификация.
get_optional_user     — мягкая аутентификация: вернёт None для анонимного.
RoleChecker           — фабрика depends-проверок по списку допустимых ролей.
"""
import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.security import decode_token
from app.database.session import get_db
from app.database.models import User
from app.services import users as users_service

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def _user_from_token(token: str, db: Session) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(token)
        email = payload.get("sub")
        token_type = payload.get("type")
        if email is None or token_type != "access":
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception

    user = users_service.get_user_by_email(db, email=email)
    if user is None:
        raise credentials_exception
    return user


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Обязательная аутентификация: 401, если токен отсутствует или невалиден."""
    return _user_from_token(token, db)


async def get_optional_user(
    request: Request,
    db: Session = Depends(get_db),
) -> User | None:
    """
    Мягкая аутентификация: если есть валидный токен — вернёт пользователя,
    иначе None. Используется для эндпоинтов с разным поведением для гостей
    и авторизованных (например, страница курса).
    """
    auth = request.headers.get("Authorization")
    if not auth or not auth.lower().startswith("bearer "):
        return None
    token = auth.split(" ", 1)[1]
    try:
        return _user_from_token(token, db)
    except HTTPException:
        return None


class RoleChecker:
    """
    Использование:
        admin_only = RoleChecker(["admin"])
        @router.post("/", dependencies=[Depends(admin_only)])
    """
    def __init__(self, allowed_roles: list[str]):
        self.allowed_roles = allowed_roles

    def __call__(self, user: User = Depends(get_current_user)) -> User:
        if user.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Operation not permitted",
            )
        return user


admin_only = RoleChecker(["admin"])
authenticated_only = RoleChecker(["user", "admin"])
