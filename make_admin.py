"""
Утилита для создания администратора с CLI.

Использование:
    python make_admin.py admin@example.com SuperSecret123 Иван Иванов или (с дефолтными значениями):
    python make_admin.py
"""
import sys
from app.database.session import SessionLocal
from app.services.users import create_user, get_user_by_email


def main() -> int:
    args = sys.argv[1:]
    email = args[0] if len(args) > 0 else "admin@example.com"
    password = args[1] if len(args) > 1 else "SuperSecret123"
    first_name = args[2] if len(args) > 2 else "Админ"
    last_name = args[3] if len(args) > 3 else "Платформы"

    db = SessionLocal()
    try:
        if get_user_by_email(db, email):
            print(f"Пользователь с email '{email}' уже существует. Пропускаю.")
            return 0
        user = create_user(
            db,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            role="admin",
        )
        print(f"Создан администратор: {user.email} (id={user.id})")
        return 0
    except Exception as e:
        print(f"Ошибка: {e}")
        return 1
    finally:
        db.close()


if __name__ == "__main__":
    raise SystemExit(main())
