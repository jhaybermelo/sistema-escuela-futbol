import math
import os

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.dependencies import get_current_user, require_admin
from app.core.logging_config import get_logger
from app.database import get_db
from app.models.alumno import Alumno
from app.models.usuario import Usuario
from app.repositories.alumno_repository import AlumnoRepository
from app.repositories.categoria_repository import CategoriaRepository
from app.repositories.school_config_repository import SchoolConfigRepository
from app.services.billing_service import BillingService
from app.services.carnet_service import generar_carnet_pdf, generar_carnet_png
from app.schemas.alumno import (
    AlumnoCreate,
    AlumnoListResponse,
    AlumnoResponse,
    AlumnoUpdate,
    GenerarHistorialResult,
    RecomputeResult,
)
from app.services.categoria_assignment_service import CategoriaAssignmentService

router = APIRouter(prefix="/alumnos", tags=["alumnos"])
logger = get_logger("alumnos", settings.LOG_DIR)


def _to_response(alumno: Alumno) -> AlumnoResponse:
    return AlumnoResponse(
        id=alumno.id,
        numero_identificacion=alumno.numero_identificacion,
        nombres=alumno.nombres,
        apellidos=alumno.apellidos,
        fecha_nacimiento=alumno.fecha_nacimiento,
        fecha_ingreso=alumno.fecha_ingreso,
        acudiente_nombre=alumno.acudiente_nombre,
        acudiente_telefono=alumno.acudiente_telefono,
        acudiente_email=alumno.acudiente_email,
        categoria_id=alumno.categoria_id,
        categoria_nombre=alumno.categoria.nombre if alumno.categoria else "",
        categoria_override=alumno.categoria_override,
        foto_path=alumno.foto_path,
        estado=alumno.estado,
    )


def _scope_categorias(usuario: Usuario) -> list[int] | None:
    """Alcance de categorías del usuario actual: None = sin restricción (admin, o
    entrenador sin categorías asignadas todavía, que ve todos los alumnos)."""
    if usuario.rol == "admin":
        return None
    ids = [c.id for c in usuario.categorias_asignadas]
    return ids or None


@router.get("", response_model=AlumnoListResponse)
async def list_alumnos(
    page: int = 1,
    size: int = 20,
    search: str | None = None,
    categoria_id: int | None = None,
    estado: str | None = None,
    db: AsyncSession = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
):
    repo = AlumnoRepository(db)
    scope = _scope_categorias(usuario)
    if scope is not None and categoria_id is not None and categoria_id not in scope:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Sin acceso a esa categoría")

    items, total = await repo.list(
        page, size, search=search, categoria_id=categoria_id, estado=estado, categoria_ids_scope=scope
    )
    return AlumnoListResponse(
        items=[_to_response(a) for a in items],
        total=total,
        page=page,
        size=size,
        pages=max(1, math.ceil(total / size)),
    )


@router.post("", response_model=AlumnoResponse, status_code=status.HTTP_201_CREATED)
async def create_alumno(
    data: AlumnoCreate,
    db: AsyncSession = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
):
    alumno_repo = AlumnoRepository(db)
    categoria_repo = CategoriaRepository(db)

    if await alumno_repo.get_by_numero_identificacion(data.numero_identificacion):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Ya existe un alumno con ese número de identificación"
        )

    if data.categoria_id is not None:
        categoria = await categoria_repo.get_by_id(data.categoria_id)
        if not categoria:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Categoría no encontrada")
        override = True
    else:
        try:
            categoria = await CategoriaAssignmentService(db).resolve_categoria(data.fecha_nacimiento)
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        override = False

    alumno = await alumno_repo.create(
        {
            **data.model_dump(exclude={"categoria_id"}),
            "categoria_id": categoria.id,
            "categoria_override": override,
            "estado": "activo",
        }
    )
    # Contrato de orden: la categoría debe quedar resuelta y visible (flush) antes de
    # generar el histórico, ya que el prorrateo depende de categoria.dias_entrenamiento.
    await db.flush()
    await db.refresh(alumno, attribute_names=["categoria"])

    config = await SchoolConfigRepository(db).get()
    await BillingService(db).generar_historial_alumno(alumno, config)

    await db.commit()
    await db.refresh(alumno, attribute_names=["categoria"])
    logger.info(f"[ALUMNO_CREADO] numero_identificacion={alumno.numero_identificacion}")
    return _to_response(alumno)


@router.post("/recompute-categorias", response_model=RecomputeResult, dependencies=[Depends(require_admin)])
async def recompute_categorias(db: AsyncSession = Depends(get_db)):
    service = CategoriaAssignmentService(db)
    cambios = await service.recompute_all()
    total = len(await AlumnoRepository(db).list_sin_override())
    await db.commit()
    logger.info(f"[RECOMPUTE_CATEGORIAS] cambios={len(cambios)}")
    return RecomputeResult(actualizados=cambios, total_revisados=total)


@router.post("/generar-historial", response_model=GenerarHistorialResult, dependencies=[Depends(require_admin)])
async def generar_historial(db: AsyncSession = Depends(get_db)):
    """Genera las mensualidades históricas faltantes de todos los alumnos activos,
    desde la fecha de inicio de la escuela (o su fecha de ingreso) hasta hoy. Útil
    tras configurar por primera vez la fecha de inicio, o para alumnos que ya
    existían en el sistema antes de este cambio."""
    config = await SchoolConfigRepository(db).get()
    resultado = await BillingService(db).generar_historial_todos(config)
    logger.info(f"[GENERAR_HISTORIAL] {resultado}")
    return GenerarHistorialResult(**resultado)


@router.get("/{alumno_id}", response_model=AlumnoResponse)
async def get_alumno(
    alumno_id: int, db: AsyncSession = Depends(get_db), usuario: Usuario = Depends(get_current_user)
):
    repo = AlumnoRepository(db)
    alumno = await repo.get_by_id(alumno_id)
    if not alumno:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alumno no encontrado")

    scope = _scope_categorias(usuario)
    if scope is not None and alumno.categoria_id not in scope:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Sin acceso a este alumno")
    return _to_response(alumno)


@router.put("/{alumno_id}", response_model=AlumnoResponse)
async def update_alumno(
    alumno_id: int,
    data: AlumnoUpdate,
    db: AsyncSession = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
):
    repo = AlumnoRepository(db)
    alumno = await repo.get_by_id(alumno_id)
    if not alumno:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alumno no encontrado")

    scope = _scope_categorias(usuario)
    if scope is not None and alumno.categoria_id not in scope:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Sin acceso a este alumno")

    update_data = data.model_dump(exclude_unset=True)
    if "categoria_id" in update_data and update_data["categoria_id"] is not None:
        categoria = await CategoriaRepository(db).get_by_id(update_data["categoria_id"])
        if not categoria:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Categoría no encontrada")
        update_data["categoria_override"] = True

    alumno = await repo.update(alumno, update_data)
    await db.commit()
    await db.refresh(alumno, attribute_names=["categoria"])
    logger.info(f"[ALUMNO_ACTUALIZADO] id={alumno_id}")
    return _to_response(alumno)


@router.post("/{alumno_id}/foto", response_model=AlumnoResponse)
async def upload_foto(
    alumno_id: int,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
):
    repo = AlumnoRepository(db)
    alumno = await repo.get_by_id(alumno_id)
    if not alumno:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alumno no encontrado")

    ext = os.path.splitext(file.filename or "")[1] or ".jpg"
    directory = os.path.join(settings.UPLOAD_DIR, "alumnos", str(alumno_id))
    os.makedirs(directory, exist_ok=True)
    file_path = os.path.join(directory, f"foto{ext}")
    with open(file_path, "wb") as f:
        f.write(await file.read())

    relative_path = f"/uploads/alumnos/{alumno_id}/foto{ext}"
    alumno = await repo.update(alumno, {"foto_path": relative_path})
    await db.commit()
    await db.refresh(alumno, attribute_names=["categoria"])
    logger.info(f"[ALUMNO_FOTO] id={alumno_id}")
    return _to_response(alumno)


@router.get("/{alumno_id}/carnet")
async def get_carnet(
    alumno_id: int,
    formato: str = "png",
    db: AsyncSession = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
):
    if formato not in ("png", "pdf"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="formato debe ser 'png' o 'pdf'")

    repo = AlumnoRepository(db)
    alumno = await repo.get_by_id(alumno_id)
    if not alumno:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alumno no encontrado")

    scope = _scope_categorias(usuario)
    if scope is not None and alumno.categoria_id not in scope:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Sin acceso a este alumno")

    config = await SchoolConfigRepository(db).get()
    await db.commit()

    if formato == "pdf":
        contenido = generar_carnet_pdf(alumno, config)
        media_type = "application/pdf"
    else:
        contenido = generar_carnet_png(alumno, config)
        media_type = "image/png"

    return Response(content=contenido, media_type=media_type)
