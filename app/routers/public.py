from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database.db import get_db
from app.schemas import TicketCreate
from app import crud
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Главная страница"""
    return templates.TemplateResponse(
        "index.html",
        {"request": request}
    )


@router.post("/api/submit-application")
async def submit_application(
    request: Request,
    ticket_data: TicketCreate,
    db: Session = Depends(get_db)
):
    """
    API endpoint для создания заявки.

    FastAPI автоматически:
    1. Парсит JSON из request body
    2. Валидирует через TicketCreate схему
    3. Преобразует projectType -> project_type (благодаря alias)
    """
    try:
        # Логируем что пришло
        body = await request.body()
        logger.info(f"Raw body: {body.decode()}")

        # Логируем что Pydantic распарсил
        logger.info(f"Parsed data: {ticket_data.model_dump()}")

        # Создаем заявку
        new_ticket = crud.create_ticket(db, ticket_data)

        logger.info(f"Заявка #{new_ticket.id} успешно создана")

        return JSONResponse(
            status_code=201,
            content={
                "success": True,
                "message": "Заявка успешно отправлена! Мы свяжемся с вами в ближайшее время.",
                "ticket_id": new_ticket.id
            }
        )

    except ValueError as e:
        logger.error(f"Ошибка валидации: {str(e)}")
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "message": f"Ошибка в данных формы: {str(e)}"
            }
        )

    except Exception as e:
        logger.error(f"Ошибка при сохранении: {str(e)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "message": "Произошла ошибка на сервере. Попробуйте позже."
            }
        )
