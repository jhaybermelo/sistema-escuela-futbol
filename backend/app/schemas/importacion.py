from datetime import date
from decimal import Decimal

from pydantic import BaseModel


class ImportAlumnoRow(BaseModel):
    fila: int
    numero_identificacion: str
    nombres: str
    apellidos: str
    fecha_nacimiento: date
    fecha_ingreso: date
    acudiente_nombre: str
    acudiente_telefono: str
    meses: dict[str, str]  # {"marzo": "", "abril": "Pagado", ...}


class ImportPeriodoPreview(BaseModel):
    periodo_inicio: date
    periodo_fin: date
    mes_columna: str | None
    monto: Decimal
    prorrateado: bool
    marcado_pagado: bool


class ImportAlumnoPreview(ImportAlumnoRow):
    categoria_nombre: str | None
    periodos: list[ImportPeriodoPreview]
    errores: list[str]
    advertencias: list[str]


class ImportPreviewResponse(BaseModel):
    filas: list[ImportAlumnoPreview]


class ImportConfirmRequest(BaseModel):
    filas: list[ImportAlumnoRow]


class ImportConfirmResultItem(BaseModel):
    fila: int
    ok: bool
    alumno_id: int | None = None
    mensualidades_generadas: int = 0
    pagos_generados: int = 0
    error: str | None = None


class ImportConfirmResponse(BaseModel):
    resultados: list[ImportConfirmResultItem]
