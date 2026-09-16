from datetime import datetime

from pydantic import BaseModel


class NotificationLogResponse(BaseModel):
    id: int
    alumno_id: int
    alumno_nombre: str
    mensualidad_id: int
    tipo: str
    canal: str
    enviado_en: datetime
    exitoso: bool
    detalle_error: str | None

    model_config = {"from_attributes": True}


class NotificationLogListResponse(BaseModel):
    items: list[NotificationLogResponse]
    total: int
    page: int
    size: int
    pages: int


class EnviarRecordatoriosResult(BaseModel):
    revisadas: int
    enviados: int
    fallidos: int
