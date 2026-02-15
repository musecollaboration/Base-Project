from fastapi import APIRouter

from app.api.v1.routers import auth, user

# Создаем главный роутер для версии v1
api_v1_router = APIRouter(prefix="/api/v1")

# Подключаем роутеры конкретных сущностей
api_v1_router.include_router(auth.router, prefix="/auth", tags=["Auth"])
api_v1_router.include_router(user.router, prefix="/users", tags=["Users"])

# Если в будущем появится v2, создашь api_v2_router здесь же
