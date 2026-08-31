"""
Auth endpoints.

Bootstrap note: the very first user ever created has no admin to promote
them, so register() makes an exception — if the users table is empty,
the first registration becomes "admin" automatically. Every registration
after that is "viewer" by default; an admin promotes people via
PATCH /auth/users/{id}/role.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.orm import Session

from api.schemas.auth import RoleUpdate, Token, UserCreate, UserResponse
from core.security import (
    create_access_token,
    get_current_user,
    hash_password,
    require_role,
    verify_password,
)
from database.models import User
from database.session import get_db

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=201)
def register(payload: UserCreate, db: Session = Depends(get_db)) -> User:
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(409, "An account with this email already exists.")

    is_first_user = db.query(User).count() == 0
    user = User(
        email=payload.email,
        hashed_password=hash_password(payload.password),
        role="admin" if is_first_user else "viewer",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)) -> Token:
    # OAuth2PasswordRequestForm's field is called "username" by spec, but we
    # authenticate by email — the frontend just puts the email in that field.
    user = db.query(User).filter(User.email == form_data.username).first()
    if user is None or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(401, "Incorrect email or password", headers={"WWW-Authenticate": "Bearer"})
    if not user.is_active:
        raise HTTPException(403, "This account has been deactivated.")

    return Token(access_token=create_access_token(subject=user.email))


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)) -> User:
    return current_user


@router.get("/users", response_model=list[UserResponse])
def list_users(db: Session = Depends(get_db), _admin: User = Depends(require_role("admin"))) -> list[User]:
    return db.execute(select(User).order_by(User.created_at)).scalars().all()


@router.patch("/users/{user_id}/role", response_model=UserResponse)
def update_user_role(
    user_id: int,
    payload: RoleUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_role("admin")),
) -> User:
    if user_id == admin.id and payload.role != "admin":
        raise HTTPException(400, "You can't demote your own account.")

    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(404, f"User {user_id} not found")
    user.role = payload.role
    db.commit()
    db.refresh(user)
    return user
