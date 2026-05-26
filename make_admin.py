from app.database.session import SessionLocal
from app.database.crud import create_user

db = SessionLocal()

try:
    user = create_user(db, email="admin@hse.ru", password="superpassword", role="admin")
    print(f"Пользователь {user.email} с ролью '{user.role}' успешно создан!")
except Exception as e:
    print(f"Ошибка: {e}")
finally:
    db.close()