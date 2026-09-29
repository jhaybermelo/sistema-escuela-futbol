from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import require_admin
from app.database import get_db
from app.models.usuario import Usuario
from app.schemas.importacion import ImportConfirmRequest, ImportConfirmResponse, ImportPreviewResponse
from app.services.importacion_service import ImportacionService

router = APIRouter(prefix="/importaciones", tags=["importaciones"], dependencies=[Depends(require_admin)])


@router.post("/alumnos/preview", response_model=ImportPreviewResponse)
async def preview_importacion_alumnos(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """Parsea y valida el CSV sin escribir nada en la base de datos, para revisar y
    corregir antes de confirmar la importación."""
    service = ImportacionService(db)
    numero_inicial = await service.siguiente_numero_identificacion()
    try:
        filas, errores_parseo, advertencias_parseo = service.parse_csv(await file.read(), numero_inicial)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    previews = await service.preview(filas, errores_parseo, advertencias_parseo)
    return ImportPreviewResponse(filas=previews)


@router.post("/alumnos/confirmar", response_model=ImportConfirmResponse)
async def confirmar_importacion_alumnos(
    data: ImportConfirmRequest,
    db: AsyncSession = Depends(get_db),
    usuario: Usuario = Depends(require_admin),
):
    """Crea los alumnos, su historial de mensualidades, y los pagos/recibos de los
    meses marcados 'Pagado', a partir de las filas ya revisadas en la previsualización."""
    service = ImportacionService(db)
    resultados = await service.confirmar(data.filas, usuario.id)
    return ImportConfirmResponse(resultados=resultados)
