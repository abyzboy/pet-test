from sqlalchemy import Integer, String
from database.db import Base
from sqlalchemy.orm import mapped_column, Mapped


class Ticket(Base):
    __tablename__ = 'tickets'
    id: Mapped[int] = mapped_column(Integer(), primary_key=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    status: Mapped[str] = mapped_column(
        String(10), default='Заявка не рассмотрена')
