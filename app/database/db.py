from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

DATABASE_URL = "sqlite:///app/database/sqlbase.db"

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(bind=engine)


class Base(DeclarativeBase):
    pass


def init_db():
    """Создание всех таблиц"""
    Base.metadata.create_all(bind=engine)


# Функция-генератор для получения сессии БД
def get_db():
    """
    Эта функция будет использоваться как зависимость в FastAPI.
    Она создает сессию, отдает её для работы, 
    а после завершения запроса - закрывает.
    """
    db = SessionLocal()
    try:
        yield db  # Отдаем сессию
    finally:
        db.close()  # Всегда закрываем после использования
