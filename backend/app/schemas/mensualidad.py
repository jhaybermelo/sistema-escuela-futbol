from datetime import date
from decimal import Decimal

from pydantic import BaseModel


class MensualidadResponse(BaseModel):
    id: int
    alumno_id: int
    alumno_nombre: str
    periodo_inicio: date
    periodo_fin: date
    monto: Decimal
    monto_prorrateado: bool
    estado: str
    fecha_vencimiento: date
    total_pagado: Decimal

    model_config = {"from_attributes": True}


class MensualidadListResponse(BaseModel):
    items: list[MensualidadResponse]
    total: int
    page: int
    size: int
    pages: int


class ResumenAlumno(BaseModel):
    alumno_id: int
    total_mensualidades: int
    pagadas: int
    pendientes: int
    vencidas: int
    meses_desde_inicio_escuela: int | None = None


class ResumenCarteraItem(BaseModel):
    pendientes: int
    vencidas: int


class ResumenCarteraResponse(BaseModel):
    por_alumno: dict[int, ResumenCarteraItem]
