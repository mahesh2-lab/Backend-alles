from fastapi import Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import Optional, cast
from src.db.init_db import get_db
from src.core.security import decode_token
from src.models.user import User


def get_current_user(
    request: Request,
    db: Session = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    # Try Authorization header first
    auth_header: Optional[str] = request.headers.get("Authorization")
    token: Optional[str] = None

    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.replace("Bearer ", "")
    else:
        # Fall back to cookie
        token = request.cookies.get("access_token")

    if not token:
        raise credentials_exception

    payload = decode_token(token)

    if payload is None or payload.get("type") != "access":
        raise credentials_exception

    email: Optional[str] = payload.get("sub")
    if email is None:
        raise credentials_exception

    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise credentials_exception

    return user

def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
        return current_user
