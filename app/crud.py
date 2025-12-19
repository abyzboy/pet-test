from passlib.context import CryptContext
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_
from app.models import Ticket, AdminUser
from app.database import db as db_s
from app.enums import TicketStatus
from app.schemas import TicketCreate, TicketUpdate, AdminUserCreate
from datetime import datetime


def create_ticket(db: Session, ticket_data: TicketCreate):
    db_ticket = Ticket(**ticket_data.model_dump())

    db.add(db_ticket)
    db.commit()
    db.refresh(db_ticket)
    return db_ticket


def get_ticket(db: Session, ticket_id: int):
    return db.query(Ticket).filter(Ticket.id == ticket_id).first()


def get_tickets(
    db: Session, skip: int = 0, limit: int = 30,
    status: TicketStatus | None = None,
    search: str | None = None
) -> list[Ticket]:
    query = db.query(Ticket)

    if status:
        query = query.filter(Ticket.status == status)

    if search:
        search_filter = or_(Ticket.name.ilike(f"%{search}%"),
                            Ticket.email.ilike(f"${search}%"))

        query = query.filter(search_filter)

    query = query.order_by(desc(Ticket.created_at))

    return query.offset(skip).limit(limit).all()


def update_ticket_status(db: Session, ticket_id: int, ticket_data: TicketUpdate):
    db_ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if db_ticket:
        db_ticket.status = ticket_data.status
        db.commit()
        db.refresh(db_ticket)
    return db_ticket


def delete_ticket(db: Session, ticket_id: int):
    db_ticket = get_ticket(db, ticket_id)
    if db_ticket:
        db.delete(db_ticket)
        db.commit()
        return True
    else:
        return False


# Контекст для хеширования паролей
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Проверяет соответствие пароля хешу"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Хеширует пароль"""
    return pwd_context.hash(password)


def create_admin(db: Session, admin_data: AdminUserCreate) -> AdminUser:
    """Создает нового админа"""
    hashed_password = get_password_hash(admin_data.password)

    db_admin = AdminUser(
        username=admin_data.username,
        email=admin_data.email,
        hashed_password=hashed_password
    )

    db.add(db_admin)
    db.commit()
    db.refresh(db_admin)

    return db_admin


def get_admin_by_username(db: Session, username: str) -> AdminUser | None:
    """Находит админа по username"""
    return db.query(AdminUser).filter(AdminUser.username == username).first()


def authenticate_admin(db: Session, username: str, password: str) -> AdminUser | None:
    """
    Проверяет логин и пароль админа.
    Возвращает объект AdminUser если успешно, None если ошибка.
    """
    admin = get_admin_by_username(db, username)

    if not admin:
        return None

    if not verify_password(password, admin.hashed_password):
        return None

    db.commit()

    return admin
