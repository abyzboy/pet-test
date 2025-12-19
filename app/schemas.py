from pydantic import BaseModel, EmailStr, Field, ConfigDict
from datetime import datetime
from app.models import Ticket
from app.enums import TicketStatus


class TicketCreate(BaseModel):
    """
    Эта схема автоматически проверят данные формы.
    Pydantic автоматически валидирует типы и форматы.
    """
    model_config = ConfigDict(populate_by_name=True)
    name: str = Field(..., min_length=3, max_length=100)
    email: EmailStr = Field(..., max_length=100)
    phone: str = Field(..., pattern=r"^\+?[\d\s\-\(\)]+$")
    message: str | None = Field(default=None)
    project_type: str | None = Field(default=None, alias="projectType")


class TicketUpdate(BaseModel):
    """Только те поля которые можно менять в админ панеле"""
    status: TicketStatus


class TicketResponse(BaseModel):
    """Полная информация о заявке"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: str
    phone: str
    status: TicketStatus
    created_at: datetime
    updated_at: datetime | None


# Схемы для админов
class AdminUserCreate(BaseModel):
    """Создание админа"""
    username: str = Field(..., min_length=3, max_length=50)
    email: str
    password: str = Field(..., min_length=8)


class AdminUserLogin(BaseModel):
    """Логин админа"""
    username: str
    password: str


class AdminUserResponse(BaseModel):
    """Ответ с данными админа (БЕЗ пароля!)"""
    model_config = ConfigDict(from_attributes=True)
    id: int
    username: str
    email: str
    created_at: datetime
