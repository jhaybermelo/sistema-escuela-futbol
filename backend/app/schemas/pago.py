from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel


class PagoResponse(BaseModel):
    id: int
    mensualidad_id: int
    monto: Decimal
    fecha_pago: date
    metodo_pago: str
    recibo_tipo: str
    recibo_path: str
    referencia: str | None
    observaciones: str | None
    token: str
    created_at: datetime

    model_config = {"from_attributes": True}


class PagoListResponse(BaseModel):
    items: list[PagoResponse]
    total: int
    page: int
    size: int
    pages: int


class ReciboConcepto(BaseModel):
    concepto: str
    descripcion: str
    monto: Decimal


class ReciboDataResponse(BaseModel):
    numero_recibo: str
    token: str
    fecha: date
    alumno_nombre: str
    categoria_nombre: str
    acudiente_nombre: str
    acudiente_telefono: str
    periodo_texto: str
    metodo_pago: str
    referencia: str | None
    observaciones: str | None
    conceptos: list[ReciboConcepto]
    total: Decimal
