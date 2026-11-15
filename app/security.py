from datetime import datetime, timedelta, timezone
from typing import Any, Union

from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.config import settings
from app.database import get_db
from app.models import User

password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/users/login")


def get_password_hash(plain_password: str) -> str:
    return password_context.hash(plain_password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return password_context.verify(plain_password, hashed_password)

def create_access_token(subject: Union[str, Any], expires_delta: timedelta = None) -> str:
    if expires_delta:
        expire_time = datetime.now(timezone.utc) + expires_delta
    else:
        expire_time = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload_to_encode = {"exp": expire_time, "sub": str(subject)}
    encoded_jwt = jwt.encode(payload_to_encode, settings.SECRET_KEY, algorithm="HS256")
    return encoded_jwt


# ==========================================
# تابع قبلی (برای کاربران عادی)
# ==========================================
def get_current_user(token: str = Depends(oauth2_scheme)) -> str:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="اعتبار توکن تایید نشد",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        user_email: str = payload.get("sub")
        if user_email is None:
            raise credentials_exception
        return user_email
    except JWTError:
        raise credentials_exception


# ==========================================
# تابع جدید: فقط ادمین‌ها اجازه عبور دارند!
# ==========================================
async def get_current_admin_user(
    current_user_email: str = Depends(get_current_user), # اول چک می‌کنیم لاگین کرده یا نه
    db: AsyncSession = Depends(get_db) # برای چک کردن نقش، به دیتابیس نیاز داریم
) -> User:
    
    # رفتن به دیتابیس و پیدا کردن کاربر
    database_query = select(User).where(User.email == current_user_email)
    result = await db.execute(database_query)
    user = result.scalar_one_or_none()
    
    # اگر کاربر وجود نداشت یا نقشش ادمین نبود، ارور 403 (ممنوع) می‌دهیم
    if not user or user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="شما دسترسی ادمین ندارید"
        )
        
    return user
  