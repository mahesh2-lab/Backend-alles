from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
from typing import cast
from src.db.init_db import get_db
from src.schemas.token import Token, UserLogin
from src.schemas.user import UserCreate, UserResponse
from src.models.user import User
from src.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token
)
from src.core.config import settings
from sqlalchemy.exc import IntegrityError
import re

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_in: UserCreate, db: Session = Depends(get_db)):

    # Basic validations
    email_regex = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
    if not re.match(email_regex, user_in.email):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid email format"
        )

    pwd = user_in.password or ""
    if len(pwd) < 8 or not re.search(r"[A-Z]", pwd) or not re.search(r"[a-z]", pwd) or not re.search(r"\d", pwd):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Password must be at least 8 characters and include uppercase, lowercase and a number"
        )

    if not re.match(r"^[A-Za-z0-9_]{3,30}$", user_in.username):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Username must be 3-30 characters and contain only letters, numbers and underscores"
        )

    if user_in.team_role is not None and (not isinstance(user_in.team_role, str) or len(user_in.team_role) > 50):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid team_role"
        )

    # Check existing user (by email or username)
    existing_user = db.query(User).filter(
        (User.email == user_in.email) | (User.username == user_in.username)
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email or username already registered"
        )

    user = User(
        email=user_in.email,
        name=user_in.name,
        username=user_in.username,
        hashed_password=get_password_hash(user_in.password),
        team_role=user_in.team_role
    )
    db.add(user)
    try:
        db.commit()
        db.refresh(user)
        return user
    except IntegrityError:
        db.rollback()
        # Handle race condition / DB unique constraint violations
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email or username already registered"
        )
    except Exception:
        db.rollback()
        # Generic error
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user"
        )


@router.post("/login", response_model=Token)
def login(credentials: UserLogin, response: Response, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == credentials.email).first()
    if not user or not verify_password(credentials.password, cast(str, user.hashed_password)):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_payload = UserResponse.model_validate(user).model_dump(mode="json")

    access_token = create_access_token(data={"sub": user.email, "user": user_payload})
    refresh_token = create_refresh_token(data={"sub": user.email, "user": user_payload})

    access_max_age = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    refresh_max_age = settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60

 
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


@router.post("/logout")
def logout(response: Response):
    # Clear cookies
    response.delete_cookie(key=settings.ACCESS_TOKEN_COOKIE_NAME, path="/")
    response.delete_cookie(key=settings.REFRESH_TOKEN_COOKIE_NAME, path="/")
    return {"msg": "Successfully logged out"}
