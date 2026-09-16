from datetime import date
from decimal import Decimal

from pydantic import BaseModel


class MetodoPagoResumen(BaseModel):
    metodo_pago: str
    total: Decimal
    cantidad: int


class PagoReporteItem(BaseModel):
    id: int
    fecha_pago: date
    alumno_nombre: str
    periodo_texto: str
    metodo_pago: str
    monto: Decimal

    model_config = {"from_attributes": True}


class ReportePagosResponse(BaseModel):
    mes: int
    anio: int
    total_general: Decimal
    cantidad_total: int
    por_metodo: list[MetodoPagoResumen]
    pagos: list[PagoReporteItem]
