# main.py
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from database.db import init_db
from models.ticket import Ticket
import logging

# Логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Инициализация FastAPI
app = FastAPI(title="ДомиЛьоны", description="Премиум строительство")

# Инициализация БД
init_db()

# Подключение статических файлов
# app.mount("/static", StaticFiles(directory="app/static"), name="static")


logger.info("✅ Приложение успешно запущено!")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
