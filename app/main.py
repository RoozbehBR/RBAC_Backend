from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.database import Base, engine
from app.routers import users, admin


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(
    title="RBAC API",
    description="سیستم احراز هویت با نقش‌های مختلف",
    version="0.1.0",
    lifespan=lifespan,
)

# وصل کردن هر دو روتر
app.include_router(users.router, prefix="/api/v1")
app.include_router(admin.router, prefix="/api/v1") # ← روتر ادمین هم وصل شد


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok"}