from fastapi import FastAPI
from app.routers import appeals

app = FastAPI(
    title="Microlearning Platform API",
    description="Backend for microlearning platform",
    version="1.0.0"
)

app.include_router(appeals.router)