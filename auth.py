from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import Optional
from jose import jwt, JWTError
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
import models
from database import SessionLocal
import os

SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 1 day

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: Optional[str]) -> bool:
    """Compare plain password with hashed one."""
    if not hashed_password:
        return False
    return pwd_context.verify(plain_password, str(hashed_password))  # ✅ cast to str


def create_access_token(
    user_id: Optional[int],
    role: Optional[str],
    expires_delta: Optional[timedelta] = None
) -> str:
    """Generate JWT token for user."""
    if user_id is None or role is None:
        raise ValueError("user_id and role cannot be None")

    to_encode = {
        "user_id": int(user_id),   # ✅ cast to int
        "role": str(role)          # ✅ cast to str
    }
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> models.User:
    """Decode token and return user object."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: Optional[int] = payload.get("user_id")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(models.User).filter(models.User.id == int(user_id)).first()  # ✅ cast id
    if user is None:
        raise credentials_exception
    return user


def require_role(*roles: str):
    """Restrict endpoint access by role."""
    allowed = [r.lower() for r in roles]

    def role_checker(current_user: models.User = Depends(get_current_user)):
        if (getattr(current_user, "role", "") or "").lower() not in allowed:
            raise HTTPException(status_code=403, detail="Operation not permitted for your role")
        return current_user

    return role_checker
