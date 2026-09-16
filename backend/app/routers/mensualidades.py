import math
from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import require_admin
from app.core.logging_config import get_logger
from app.config import settings
from app.database import get_db
from app.models.mensualidad import Mensualidad
from app.models.usuario import Usuario
from app.repositories.mensualidad_repository import MensualidadRepository
from app.repositories.pago_repository import PagoRepository
from app.repositories.school_config_repository import SchoolConfigRepository
from app.schemas.alumno import GenerarHistorialResult
from app.schemas.mensualidad import (
    MensualidadListResponse,
    MensualidadResponse,
    ResumenAlumno,
    ResumenCarteraItem,
    ResumenCarteraResponse,
)
from app.services.billing_service import BillingService

router = APIRouter(prefix="/mensualidades", tags=["mensualidades"], dependencies=[Depends(require_admin)])
logger = get_logger("facturacion", settings.LOG_DIR)


def _to_response(mensualidad: Mensualidad, total_pagado: Decimal | None = None) -> MensualidadResponse:
    """`total_pagado` se puede pasar explícito (consulta agregada fresca) para evitar
    depender de la colección `mensualidad.pagos` cacheada en el identity map de la
    sesión, que puede quedar desactualizada tras un delete/insert de Pago dentro de
    la misma request (ver marcar_pagado/marcar_pendiente)."""
    if total_pagado is None:
        total_pagado = sum((p.monto for p in mensualidad.pagos), Decimal("0"))
    return MensualidadResponse(
        id=mensualidad.id,
        alumno_id=mensualidad.alumno_id,
        alumno_nombre=f"{mensualidad.alumno.nombres} {mensualidad.alumno.apellidos}",
        periodo_inicio=mensualidad.periodo_inicio,
        periodo_fin=mensualidad.periodo_fin,
        monto=mensualidad.monto,
        monto_prorrateado=mensualidad.monto_prorrateado,
        estado=mensualidad.estado,
        fecha_vencimiento=mensualidad.fecha_vencimiento,
        total_pagado=total_pagado,
    )


@router.get("", response_model=MensualidadListResponse)
async def list_mensualidades(
    page: int = 1,
    size: int = 20,
    alumno_id: int | None = None,
    estado: str | None = None,
    categoria_id: int | None = None,
    search: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    repo = MensualidadRepository(db)
    items, total = await repo.list(
        page, size, alumno_id=alumno_id, estado=estado, categoria_id=categoria_id, search=search
    )
    return MensualidadListResponse(
        items=[_to_response(m) for m in items],
        total=total,
        page=page,
        size=size,
        pages=max(1, math.ceil(total / size)),
    )


@router.get("/alumno/{alumno_id}/resumen", response_model=ResumenAlumno)
async def resumen_alumno(alumno_id: int, db: AsyncSession = Depends(get_db)):
    repo = MensualidadRepository(db)
    resumen = await repo.resumen_por_alumno(alumno_id)

    config = await SchoolConfigRepository(db).get()
    await db.commit()
    meses_desde_inicio_escuela = None
    if config.fecha_inicio:
        periodos = BillingService._periodos_en_rango(config.dia_corte, config.fecha_inicio, date.today())
        meses_desde_inicio_escuela = len(periodos)

    return ResumenAlumno(
        alumno_id=alumno_id, meses_desde_inicio_escuela=meses_desde_inicio_escuela, **resumen
    )


@router.get("/resumen-cartera", response_model=ResumenCarteraResponse)
async def resumen_cartera(db: AsyncSession = Depends(get_db)):
    """Conteo de mensualidades pendientes/vencidas por alumno, para mostrar el
    estado de cartera de un vistazo en la lista de Alumnos."""
    repo = MensualidadRepository(db)
    resumen = await repo.resumen_cartera()
    return ResumenCarteraResponse(
        por_alumno={
            alumno_id: ResumenCarteraItem(**conteo) for alumno_id, conteo in resumen.items()
        }
    )


@router.post("/generar-periodo", response_model=GenerarHistorialResult)
async def generar_periodo(db: AsyncSession = Depends(get_db)):
    """Genera, para cada alumno activo, todas las mensualidades faltantes desde su
    fecha de ingreso (o la fecha de inicio de la escuela, la que sea más tardía)
    hasta hoy — no solo el periodo actual. Idempotente."""
    config = await SchoolConfigRepository(db).get()
    service = BillingService(db)
    resultado = await service.generar_historial_todos(config)
    return GenerarHistorialResult(
        alumnos_revisados=resultado["alumnos_revisados"],
        mensualidades_generadas=resultado["mensualidades_generadas"],
    )


@router.post("/marcar-vencidas")
async def marcar_vencidas(db: AsyncSession = Depends(get_db)):
    service = BillingService(db)
    total = await service.marcar_vencidas()
    return {"vencidas": total}


@router.get("/{mensualidad_id}", response_model=MensualidadResponse)
async def get_mensualidad(mensualidad_id: int, db: AsyncSession = Depends(get_db)):
    repo = MensualidadRepository(db)
    mensualidad = await repo.get_by_id(mensualidad_id)
    if not mensualidad:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mensualidad no encontrada")
    return _to_response(mensualidad)


@router.post("/{mensualidad_id}/marcar-pagado", response_model=MensualidadResponse)
async def marcar_pagado(
    mensualidad_id: int, db: AsyncSession = Depends(get_db), usuario: Usuario = Depends(require_admin)
):
    """Marcado rápido para meses históricos: registra el saldo pendiente como pagado
    en efectivo, sin recibo (recibo_tipo='historico'), y deja la mensualidad en
    estado 'pagado'. Pensado para reconstruir el histórico de pagos anteriores al
    sistema, no reemplaza el flujo normal de registrar un pago con recibo."""
    mensualidad_repo = MensualidadRepository(db)
    pago_repo = PagoRepository(db)

    mensualidad = await mensualidad_repo.get_by_id(mensualidad_id)
    if not mensualidad:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mensualidad no encontrada")

    total_pagado = await pago_repo.total_pagado(mensualidad_id)
    saldo = mensualidad.monto - total_pagado
    if saldo > 0:
        await pago_repo.create(
            {
                "mensualidad_id": mensualidad_id,
                "monto": saldo,
                "fecha_pago": min(mensualidad.fecha_vencimiento, date.today()),
                "metodo_pago": "efectivo",
                "recibo_tipo": "historico",
                "recibo_path": "",
                "registrado_por": usuario.id,
            }
        )

    mensualidad = await mensualidad_repo.update(mensualidad, {"estado": "pagado"})
    await db.commit()
    mensualidad = await mensualidad_repo.get_by_id(mensualidad_id)
    total_pagado_final = await pago_repo.total_pagado(mensualidad_id)
    logger.info(f"[MENSUALIDAD_MARCADA_PAGADA] id={mensualidad_id}")
    return _to_response(mensualidad, total_pagado_final)


@router.post("/{mensualidad_id}/marcar-pendiente", response_model=MensualidadResponse)
async def marcar_pendiente(mensualidad_id: int, db: AsyncSession = Depends(get_db)):
    """Deshace un 'marcar como pagado' histórico: elimina el pago sin recibo que se
    generó al marcarlo, y recalcula el estado real según lo efectivamente pagado."""
    mensualidad_repo = MensualidadRepository(db)
    pago_repo = PagoRepository(db)

    mensualidad = await mensualidad_repo.get_by_id(mensualidad_id)
    if not mensualidad:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mensualidad no encontrada")

    await pago_repo.delete_historicos(mensualidad_id)
    total_pagado = await pago_repo.total_pagado(mensualidad_id)

    if total_pagado >= mensualidad.monto:
        nuevo_estado = "pagado"
    elif total_pagado > 0:
        nuevo_estado = "parcial"
    elif mensualidad.fecha_vencimiento < date.today():
        nuevo_estado = "vencido"
    else:
        nuevo_estado = "pendiente"

    mensualidad = await mensualidad_repo.update(mensualidad, {"estado": nuevo_estado})
    await db.commit()
    mensualidad = await mensualidad_repo.get_by_id(mensualidad_id)
    total_pagado_final = await pago_repo.total_pagado(mensualidad_id)
    logger.info(f"[MENSUALIDAD_MARCADA_PENDIENTE] id={mensualidad_id}")
    return _to_response(mensualidad, total_pagado_final)
