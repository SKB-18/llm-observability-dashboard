"""
Authentication routes: register, login, me.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from backend.auth import (
    create_access_token,
    get_current_user,
    hash_password,
    verify_password,
)
from backend.database import get_db
from backend.models import User

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------
class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    is_active: bool

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(body: RegisterRequest, db: Session = Depends(get_db)):
    """Create a new user account."""
    if db.query(User).filter(User.username == body.username).first():
        raise HTTPException(status_code=409, detail="Username already taken.")
    if db.query(User).filter(User.email == body.email).first():
        raise HTTPException(status_code=409, detail="Email already registered.")

    user = User(
        username=body.username,
        email=body.email,
        hashed_password=hash_password(body.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=TokenResponse)
def login(
    form: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """Exchange username + password for a JWT access token."""
    user = db.query(User).filter(User.username == form.username).first()
    if not user or not verify_password(form.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is disabled.")

    token = create_access_token({"sub": user.username})
    return {"access_token": token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)):
    """Return the currently authenticated user's profile."""
    return current_user


@router.post("/logout")
def logout():
    """Client-side logout — instruct client to discard the token."""
    return {"message": "Logged out. Discard your token on the client."}
