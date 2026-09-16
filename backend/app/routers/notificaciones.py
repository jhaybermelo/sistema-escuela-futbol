import math

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import require_admin
from app.core.logging_config import get_logger
from app.config import settings
from app.database import get_db
from app.models.notification_log import NotificationLog
from app.repositories.notification_log_repository import NotificationLogRepository
from app.schemas.notification_log import (
    EnviarRecordatoriosResult,
    NotificationLogListResponse,
    NotificationLogResponse,
)
from app.services.reminder_service import ReminderService

router = APIRouter(prefix="/notificaciones", tags=["notificaciones"], dependencies=[Depends(require_admin)])
logger = get_logger("notificaciones", settings.LOG_DIR)


def _to_response(registro: NotificationLog) -> NotificationLogResponse:
    return NotificationLogResponse(
        id=registro.id,
        alumno_id=registro.alumno_id,
        alumno_nombre=f"{registro.alumno.nombres} {registro.alumno.apellidos}",
        mensualidad_id=registro.mensualidad_id,
        tipo=registro.tipo,
        canal=registro.canal,
        enviado_en=registro.enviado_en,
        exitoso=registro.exitoso,
        detalle_error=registro.detalle_error,
    )


@router.get("", response_model=NotificationLogListResponse)
async def list_notificaciones(
    page: int = 1,
    size: int = 20,
    alumno_id: int | None = None,
    tipo: str | None = None,
    canal: str | None = None,
    exitoso: bool | None = None,
    db: AsyncSession = Depends(get_db),
):
    repo = NotificationLogRepository(db)
    items, total = await repo.list(page, size, alumno_id=alumno_id, tipo=tipo, canal=canal, exitoso=exitoso)
    return NotificationLogListResponse(
        items=[_to_response(r) for r in items],
        total=total,
        page=page,
        size=size,
        pages=max(1, math.ceil(total / size)),
    )


@router.post("/enviar-recordatorios", response_model=EnviarRecordatoriosResult)
async def enviar_recordatorios(db: AsyncSession = Depends(get_db)):
    service = ReminderService(db)
    resultado = await service.enviar_recordatorios()
    return EnviarRecordatoriosResult(**resultado)
