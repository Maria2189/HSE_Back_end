from fastapi import FastAPI
from app.routers import appeals, students # Импортируем новый роутер
from app.database.session import engine
from app.database import models
from app.routers import auth

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Microlearning Platform API")

app.include_router(appeals.router)
app.include_router(students.router)

@app.get("/")
def root():
    return {"message": "Welcome to Microlearning Platform API"}

app.include_router(auth.router)