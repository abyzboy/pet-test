from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app.database.db import engine, Base
from app.models import Ticket
from app.routers import public, admin
import logging

Base.metadata.create_all(bind=engine)
# Инициализируем FastAPI приложение
app = FastAPI(
    title="ДомиЛьоны - Система заявок",
    description="Backend для сайта строительной компании",
    version="1.0.0"
)
# Подключаем статические файлы (CSS, JS, изображения)
# Если у тебя есть папка static с CSS/JS - раскомментируй:
# app.mount("/static", StaticFiles(directory="static"), name="static")

# Подключаем роутеры
# Публичная часть (главная страница, API для заявок)
app.include_router(public.router, tags=["Public"])

# Админка (будем делать дальше)
app.include_router(admin.router, tags=["Admin"])

# Корневой endpoint для проверки что сервер работает


@app.get("/health")
async def health_check():
    """
    Простая проверка здоровья сервера.
    Полезно для мониторинга.
    """
    return {
        "status": "ok",
        "message": "Сервер работает"
    }

# Это запустится при старте приложения


@app.on_event("startup")
async def startup_event():
    """
    Выполняется когда сервер запускается.
    Здесь можно инициализировать соединения, кеши и т.д.
    """
    print("🚀 Сервер ДомиЛьоны запущен!")
    print("📝 Документация API: http://127.0.0.1:8000/docs")


@app.on_event("shutdown")
async def shutdown_event():
    """
    Выполняется при остановке сервера.
    Закрываем соединения, сохраняем данные и т.д.
    """
    print("👋 Сервер остановлен")
