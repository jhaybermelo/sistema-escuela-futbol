from decimal import Decimal

from pydantic import BaseModel


class CategoriaConteo(BaseModel):
    categoria_nombre: str
    total: int


class DashboardResumen(BaseModel):
    alumnos_activos: int
    alumnos_por_categoria: list[CategoriaConteo]
    ingresos_mes: Decimal | None = None
    mensualidades_pendientes: int | None = None
    mensualidades_vencidas: int | None = None
