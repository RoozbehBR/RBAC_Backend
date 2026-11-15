from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User
from app.schemas import UserCreate
from app.security import get_password_hash


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    database_query = select(User).where(User.email == email)
    result = await db.execute(database_query)
    return result.scalar_one_or_none()


async def create_user(db: AsyncSession, user_data: UserCreate) -> User:
    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        email=user_data.email,
        hashed_password=hashed_password
        # نقش (role) به صورت پیش‌فرض "user" است
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user


# ==========================================
# توابع جدید مخصوص ادمین
# ==========================================

async def get_all_users(db: AsyncSession) -> list[User]:
    # گرفتن لیست همه کاربران (فقط ادمین به این تابع دسترسی دارد)
    database_query = select(User).order_by(User.id.desc())
    result = await db.execute(database_query)
    return list(result.scalars().all())


async def ban_user_account(db: AsyncSession, target_user: User) -> User:
    # مسدود کردن یک کاربر (تغییر is_active به False)
    target_user.is_active = False
    db.add(target_user)
    await db.commit()
    await db.refresh(target_user)
    return target_user