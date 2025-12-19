from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.database.db import get_db
from app import crud
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional
from zoneinfo import ZoneInfo
# Настройки JWT
SECRET_KEY = "your-secret-key-change-this-in-production"  # ИЗМЕНИ В ПРОДАКШЕНЕ!
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 480  # 8 часов

# Security scheme для JWT
security = HTTPBearer()


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Создает JWT токен.

    data - данные для токена (обычно {"sub": username})
    expires_delta - время жизни токена
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(ZoneInfo('Europe/Moscow')) + expires_delta
    else:
        expire = datetime.now(ZoneInfo('Europe/Moscow')) + \
            timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    return encoded_jwt


def get_current_admin(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """
    Зависимость для защищенных эндпоинтов админки.

    Извлекает токен из заголовка Authorization: Bearer <token>
    Проверяет токен и возвращает объект админа.

    Использование:
    @router.get("/admin/dashboard")
    async def dashboard(admin = Depends(get_current_admin)):
        return {"admin": admin.username}
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Не удалось проверить учетные данные",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # Извлекаем токен
        token = credentials.credentials

        # Декодируем JWT
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")

        if username is None:
            raise credentials_exception

    except JWTError:
        raise credentials_exception

    # Находим админа в БД
    admin = crud.get_admin_by_username(db, username=username)

    if admin is None or not admin.is_active:
        raise credentials_exception

    return admin

# Альтернативная проверка через cookies (для HTML страниц)


def get_current_admin_from_cookie(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Зависимость для HTML страниц админки.

    Проверяет токен из cookie вместо заголовка.
    Удобно для обычных HTML страниц (не API).
    """
    token = request.cookies.get("admin_token")

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Необходима авторизация"
        )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")

        if username is None:
            raise HTTPException(status_code=401, detail="Неверный токен")

    except JWTError:
        raise HTTPException(status_code=401, detail="Неверный токен")

    admin = crud.get_admin_by_username(db, username=username)

    return admin
