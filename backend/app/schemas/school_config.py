from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field


class SchoolConfigUpdate(BaseModel):
    nombre_escuela: str | None = None
    valor_mensualidad: Decimal | None = Field(default=None, ge=0)
    dia_corte: int | None = Field(default=None, ge=1, le=28)
    dias_recordatorio_previo: int | None = Field(default=None, ge=0, le=30)
    fecha_inicio: date | None = None


class SchoolConfigResponse(BaseModel):
    nombre_escuela: str
    valor_mensualidad: Decimal
    dia_corte: int
    dias_recordatorio_previo: int
    fecha_inicio: date | None

    model_config = {"from_attributes": True}
