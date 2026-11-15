from fastapi import APIRouter, Depends, HTTPException, status as http_status
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import get_all_users, get_user_by_email, ban_user_account
from app.database import get_db
from app.schemas import UserResponse
from app.security import get_current_admin_user
from app.models import User

# این روتر فقط برای ادمین‌هاست
router = APIRouter(prefix="/admin", tags=["Admin Only"])


@router.get("/users", response_model=list[UserResponse])
async def admin_get_all_users(
    admin_user: User = Depends(get_current_admin_user), # ← درِ ادمین!
    db: AsyncSession = Depends(get_db)
):
    return await get_all_users(db)


@router.patch("/users/{user_id}/ban", response_model=UserResponse)
async def admin_ban_user(
    user_id: int,
    admin_user: User = Depends(get_current_admin_user), # ← درِ ادمین!
    db: AsyncSession = Depends(get_db)
):
    # پیدا کردن کاربری که قرار است مسدود شود
    target_user = await get_user_by_email(db, "temp") # اینجا باید با ID پیدا کنیم
    # (برای سادگی، فرض می‌کنیم یه تابع get_user_by_id داریم، ولی چون فعلا نداریم، از یه کوئری ساده استفاده می‌کنیم)
    
    from sqlalchemy import select
    result = await db.execute(select(User).where(User.id == user_id))
    target_user = result.scalar_one_or_none()
    
    if not target_user:
        raise HTTPException(status_code=404, detail="کاربر پیدا نشد")
        
    return await ban_user_account(db, target_user)