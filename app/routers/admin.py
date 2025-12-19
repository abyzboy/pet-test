from fastapi import APIRouter, Depends, Request, Form, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database.db import get_db
from app.models import AdminUser
from app.schemas import (
    AdminUserLogin,
    TicketUpdate,
)
from app import crud
from app.dependencies import (
    get_current_admin_from_cookie,
    create_access_token,
    get_current_admin
)
from app.enums import TicketStatus
from datetime import timedelta
import logging
import shutil
import os
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["Admin"])
templates = Jinja2Templates(directory="templates")

# Настройка папки для загрузки файлов
UPLOAD_DIR = Path("static/uploads/projects")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# ============= АВТОРИЗАЦИЯ =============


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """
    Страница входа в админку.

    Если админ уже залогинен (есть валидная кука) - редирект на дашборд.
    """
    # Проверяем есть ли уже токен
    token = request.cookies.get("admin_token")
    if token:
        try:
            # Если токен валидный - сразу на дашборд
            db = next(get_db())
            admin = get_current_admin_from_cookie(request, db)
            if admin:
                return RedirectResponse(url="/admin/dashboard", status_code=303)
        except:
            pass  # Токен невалидный - показываем форму входа

    return templates.TemplateResponse(
        "admin/login.html",
        {"request": request}
    )


@router.post("/login")
async def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    """
    Обработка формы входа.

    1. Проверяет логин/пароль
    2. Создает JWT токен
    3. Устанавливает cookie с токеном
    4. Редирект на дашборд
    """
    # Проверяем учетные данные
    admin = crud.authenticate_admin(db, username, password)

    if not admin:
        return templates.TemplateResponse(
            "admin/login.html",
            {
                "request": request,
                "error": "Неверный логин или пароль"
            }
        )

    # Создаем JWT токен
    access_token = create_access_token(
        data={"sub": admin.username},
        expires_delta=timedelta(hours=8)
    )

    # Создаем ответ с редиректом
    response = RedirectResponse(url="/admin/dashboard", status_code=303)

    # Устанавливаем cookie с токеном
    response.set_cookie(
        key="admin_token",
        value=access_token,
        httponly=True,  # Защита от XSS
        max_age=28800,  # 8 часов в секундах
        samesite="lax"  # CSRF защита
    )

    logger.info(f"Админ {admin.username} вошел в систему")

    return response


@router.get("/logout")
async def logout():
    """
    Выход из админки.

    Удаляет cookie с токеном и редирект на страницу входа.
    """
    response = RedirectResponse(url="/admin/login", status_code=303)
    response.delete_cookie(key="admin_token")
    return response

# ============= ДАШБОРД =============


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    db: Session = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin_from_cookie)
):
    """
    Главная страница админки.

    Показывает общую статистику:
    - Количество заявок по статусам
    - Количество проектов
    - Последние заявки
    """
    # Статистика по заявкам
    tickets_stats = {}
    for status in TicketStatus:
        count = db.query(crud.Ticket).filter(
            crud.Ticket.status == status).count()
        tickets_stats[status.value] = count

    total_tickets = sum(tickets_stats.values())

    # Последние 5 заявок
    recent_tickets = crud.get_tickets(db, limit=5)

    return templates.TemplateResponse(
        "admin/dashboard.html",
        {
            "request": request,
            "admin": admin,
            "tickets_stats": tickets_stats,
            "total_tickets": total_tickets,
            "recent_tickets": recent_tickets
        }
    )

# ============= УПРАВЛЕНИЕ ЗАЯВКАМИ =============


@router.get("/tickets", response_class=HTMLResponse)
async def tickets_page(
    request: Request,
    status: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin_from_cookie)
):
    """
    Страница со списком всех заявок.

    Поддерживает фильтрацию по статусу и поиск.
    """
    # Преобразуем строку статуса в Enum
    status_filter = None
    if status:
        try:
            status_filter = TicketStatus(status)
        except ValueError:
            pass
    logger.info(status)
    # Получаем заявки с фильтрами
    tickets = crud.get_tickets(
        db,
        status=status_filter,
        search=search,
        limit=100
    )

    # Все статусы для фильтра
    all_statuses = [s.value for s in TicketStatus]
    logger.info(all_statuses)
    return templates.TemplateResponse(
        "admin/tickets.html",
        {
            "request": request,
            "admin": admin,
            "tickets": tickets,
            "all_statuses": all_statuses,
            "current_status": status,
            "search_query": search or ""
        }
    )


@router.get("/tickets/{ticket_id}", response_class=HTMLResponse)
async def ticket_detail(
    request: Request,
    ticket_id: int,
    db: Session = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin_from_cookie)
):
    """Детальная страница одной заявки"""
    ticket = crud.get_ticket(db, ticket_id)

    if not ticket:
        raise HTTPException(status_code=404, detail="Заявка не найдена")

    all_statuses = [s.value for s in TicketStatus]

    return templates.TemplateResponse(
        "admin/ticket_detail.html",
        {
            "request": request,
            "admin": admin,
            "ticket": ticket,
            "all_statuses": all_statuses
        }
    )


@router.post("/tickets/{ticket_id}/status")
async def update_ticket_status(
    ticket_id: int,
    status: str = Form(...),
    db: Session = Depends(get_db),
    admin: AdminUser = Depends(get_current_admin_from_cookie)
):
    """
    Обновление статуса заявки.

    Вызывается из формы на странице заявки.
    """
    try:
        new_status = TicketStatus(status)
        update_data = TicketUpdate(status=new_status)

        updated_ticket = crud.update_ticket_status(db, ticket_id, update_data)

        if not updated_ticket:
            raise HTTPException(status_code=404, detail="Заявка не найдена")

        logger.info(
            f"Админ {admin.username} изменил статус заявки #{ticket_id} на {status}")

        return RedirectResponse(
            url=f"/admin/tickets/{ticket_id}",
            status_code=303
        )

    except ValueError:
        raise HTTPException(status_code=400, detail="Неверный статус")
