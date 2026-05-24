from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.schemas.auth import UserCreate, Token
from app.database import crud
from app.core.security import verify_password, create_access_token, create_refresh_token

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
def register(user: UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    new_user = crud.create_user(db, email=user.email, password=user.password, role="readonly")
    
    access_token = create_access_token(data={"sub": new_user.email, "role": new_user.role})
    refresh_token = create_refresh_token(data={"sub": new_user.email})
    
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}

@router.post("/login", response_model=Token)
def login(user: UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_email(db, email=user.email)
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(data={"sub": db_user.email, "role": db_user.role})
    refresh_token = create_refresh_token(data={"sub": db_user.email})
    
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}

@router.post("/logout")
def logout():
    return {"message": "Successfully logged out. Please remove tokens from client."}