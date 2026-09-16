from calendar import monthrange
from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import require_admin
from app.database import get_db
from app.repositories.pago_repository import PagoRepository
from app.schemas.reporte import MetodoPagoResumen, PagoReporteItem, ReportePagosResponse

router = APIRouter(prefix="/reportes", tags=["reportes"], dependencies=[Depends(require_admin)])


@router.get("/pagos", response_model=ReportePagosResponse)
async def reporte_pagos(mes: int, anio: int, db: AsyncSession = Depends(get_db)):
    if not 1 <= mes <= 12:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="mes debe estar entre 1 y 12")

    desde = date(anio, mes, 1)
    hasta = date(anio, mes, monthrange(anio, mes)[1])

    repo = PagoRepository(db)
    pagos = await repo.list_por_rango(desde, hasta)
    resumen = await repo.resumen_por_metodo(desde, hasta)

    por_metodo = [
        MetodoPagoResumen(metodo_pago=metodo, total=total, cantidad=cantidad) for metodo, total, cantidad in resumen
    ]

    return ReportePagosResponse(
        mes=mes,
        anio=anio,
        total_general=sum((m.total for m in por_metodo), Decimal(0)),
        cantidad_total=sum(m.cantidad for m in por_metodo),
        por_metodo=por_metodo,
        pagos=[PagoReporteItem.model_validate(p) for p in pagos],
    )
