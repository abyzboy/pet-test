from sqlalchemy import String, Integer, Enum as SQLEnum
from datetime import datetime
from app.database.db import Base
from sqlalchemy.orm import mapped_column, Mapped
from app.enums import TicketStatus
from zoneinfo import ZoneInfo


class Ticket(Base):
    """Таблица заявок"""
    __tablename__ = 'tickets'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    email: Mapped[str] = mapped_column(String, nullable=False, index=True)

    name: Mapped[str] = mapped_column(String, nullable=False)

    phone: Mapped[str] = mapped_column(String, nullable=False)

    status: Mapped[TicketStatus] = mapped_column(
        SQLEnum(TicketStatus), default=TicketStatus.new)

    message: Mapped[str] = mapped_column(String, nullable=True)

    project_type: Mapped[str] = mapped_column(String, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(ZoneInfo('Europe/Moscow')))
    updated_at: Mapped[datetime | None] = mapped_column(
        default=None, onupdate=lambda: datetime.now(ZoneInfo('Europe/Moscow')))


class AdminUser(Base):
    """Таблица админ пользователей"""
    __tablename__ = 'admin_users'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    username: Mapped[str] = mapped_column(String, nullable=False)

    hashed_password: Mapped[int] = mapped_column(Integer, nullable=False)

    # meta_data
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(ZoneInfo('Europe/Moscow')))
