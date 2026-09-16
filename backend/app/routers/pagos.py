import math
import os
from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.date_utils import formatear_periodo
from app.core.dependencies import require_admin
from app.core.logging_config import get_logger
from app.config import settings
from app.database import get_db
from app.models.usuario import Usuario
from app.repositories.mensualidad_repository import MensualidadRepository
from app.repositories.pago_repository import PagoRepository
from app.schemas.pago import PagoListResponse, PagoResponse, ReciboDataResponse
from app.services.recibo_service import pago_to_recibo_data

router = APIRouter(prefix="/pagos", tags=["pagos"], dependencies=[Depends(require_admin)])
logger = get_logger("facturacion", settings.LOG_DIR)

RECIBO_TIPOS = {"generado", "subido"}
METODO_PAGOS = {"efectivo", "transferencia", "nequi", "otro"}


@router.post("", response_model=PagoResponse, status_code=status.HTTP_201_CREATED)
async def create_pago(
    mensualidad_id: int = Form(...),
    monto: Decimal = Form(...),
    fecha_pago: date = Form(...),
    metodo_pago: str = Form(...),
    recibo_tipo: str = Form(...),
    referencia: str | None = Form(None),
    observaciones: str | None = Form(None),
    file: UploadFile | None = File(None),
    db: AsyncSession = Depends(get_db),
    usuario: Usuario = Depends(require_admin),
):
    if recibo_tipo not in RECIBO_TIPOS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="recibo_tipo inválido")
    if metodo_pago not in METODO_PAGOS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="metodo_pago inválido")
    if recibo_tipo == "subido" and file is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Debe adjuntar el documento del recibo físico"
        )
    if monto <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El monto debe ser mayor a cero")

    mensualidad_repo = MensualidadRepository(db)
    mensualidad = await mensualidad_repo.get_by_id(mensualidad_id)
    if not mensualidad:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mensualidad no encontrada")

    alumno = mensualidad.alumno
    periodo_texto = formatear_periodo(mensualidad.periodo_inicio, mensualidad.periodo_fin)

    pago_repo = PagoRepository(db)
    pago = await pago_repo.create(
        {
            "mensualidad_id": mensualidad_id,
            "monto": monto,
            "fecha_pago": fecha_pago,
            "metodo_pago": metodo_pago,
            "recibo_tipo": recibo_tipo,
            "recibo_path": "",
            "referencia": referencia or None,
            "observaciones": observaciones or None,
            "alumno_nombre": f"{alumno.nombres} {alumno.apellidos}",
            "categoria_nombre": alumno.categoria.nombre if alumno.categoria else "",
            "acudiente_nombre": alumno.acudiente_nombre,
            "acudiente_telefono": alumno.acudiente_telefono,
            "periodo_texto": periodo_texto,
            "conceptos": [
                {
                    "concepto": "Mensualidad",
                    "descripcion": f"Mensualidad Escuela de Fútbol - {periodo_texto}",
                    "monto": str(monto),
                }
            ],
            "registrado_por": usuario.id,
        }
    )

    if recibo_tipo == "subido":
        directory = os.path.join(settings.UPLOAD_DIR, "recibos")
        os.makedirs(directory, exist_ok=True)
        ext = os.path.splitext(file.filename or "")[1] or ".pdf"
        file_path = os.path.join(directory, f"pago-{pago.id}{ext}")
        with open(file_path, "wb") as f:
            f.write(await file.read())
        pago = await pago_repo.update(pago, {"recibo_path": f"/uploads/recibos/pago-{pago.id}{ext}"})
    # recibo_tipo == "generado": sin archivo físico — se ve/imprime en vivo en
    # /recibos/{id} del frontend, con la plantilla oficial y los datos ya guardados.

    total_pagado = await pago_repo.total_pagado(mensualidad_id)
    if total_pagado >= mensualidad.monto:
        nuevo_estado = "pagado"
    elif total_pagado > 0:
        nuevo_estado = "parcial"
    else:
        nuevo_estado = "pendiente"
    await mensualidad_repo.update(mensualidad, {"estado": nuevo_estado})

    await db.commit()
    await db.refresh(pago)
    logger.info(f"[PAGO_REGISTRADO] mensualidad_id={mensualidad_id} monto={monto} tipo={recibo_tipo}")
    return pago


@router.get("", response_model=PagoListResponse)
async def list_pagos(
    page: int = 1, size: int = 20, mensualidad_id: int | None = None, db: AsyncSession = Depends(get_db)
):
    repo = PagoRepository(db)
    items, total = await repo.list(page, size, mensualidad_id=mensualidad_id)
    return PagoListResponse(
        items=items, total=total, page=page, size=size, pages=max(1, math.ceil(total / size))
    )


@router.get("/{pago_id}", response_model=PagoResponse)
async def get_pago(pago_id: int, db: AsyncSession = Depends(get_db)):
    repo = PagoRepository(db)
    pago = await repo.get_by_id(pago_id)
    if not pago:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pago no encontrado")
    return pago


@router.get("/{pago_id}/recibo-data", response_model=ReciboDataResponse)
async def get_recibo_data(pago_id: int, db: AsyncSession = Depends(get_db)):
    """Datos del recibo oficial (plantilla Yiverth Estrella), tal como quedaron
    guardados al momento del pago — no se recalculan desde el alumno actual."""
    repo = PagoRepository(db)
    pago = await repo.get_by_id(pago_id)
    if not pago:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pago no encontrado")

    return pago_to_recibo_data(pago)


@router.get("/{pago_id}/recibo")
async def download_recibo(pago_id: int, db: AsyncSession = Depends(get_db)):
    """Descarga el archivo físico subido (recibo_tipo='subido'). Los recibos
    'generado' no tienen archivo: se ven e imprimen en /recibos/{id}."""
    repo = PagoRepository(db)
    pago = await repo.get_by_id(pago_id)
    if not pago:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pago no encontrado")
    if not pago.recibo_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Este pago no tiene un archivo de recibo asociado"
        )

    relative_path = pago.recibo_path.removeprefix("/uploads/")
    file_path = os.path.join(settings.UPLOAD_DIR, relative_path)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Archivo de recibo no encontrado")
    return FileResponse(file_path)
