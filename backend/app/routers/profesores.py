import math

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import require_admin
from app.core.logging_config import get_logger
from app.config import settings
from app.database import get_db
from app.models.profesor import Profesor
from app.repositories.categoria_repository import CategoriaRepository
from app.repositories.profesor_repository import ProfesorRepository
from app.schemas.profesor import (
    AsignarCategoriasProfesorRequest,
    ProfesorCreate,
    ProfesorListResponse,
    ProfesorResponse,
    ProfesorUpdate,
)

router = APIRouter(prefix="/profesores", tags=["profesores"], dependencies=[Depends(require_admin)])
logger = get_logger("usuarios", settings.LOG_DIR)


def _to_response(profesor: Profesor) -> ProfesorResponse:
    return ProfesorResponse(
        id=profesor.id,
        nombre=profesor.nombre,
        telefono=profesor.telefono,
        activo=profesor.activo,
        categoria_ids=[c.id for c in profesor.categorias],
    )


@router.get("", response_model=ProfesorListResponse)
async def list_profesores(page: int = 1, size: int = 20, db: AsyncSession = Depends(get_db)):
    repo = ProfesorRepository(db)
    items, total = await repo.list(page, size)
    return ProfesorListResponse(
        items=[_to_response(p) for p in items],
        total=total,
        page=page,
        size=size,
        pages=max(1, math.ceil(total / size)),
    )


@router.post("", response_model=ProfesorResponse, status_code=status.HTTP_201_CREATED)
async def create_profesor(data: ProfesorCreate, db: AsyncSession = Depends(get_db)):
    repo = ProfesorRepository(db)
    profesor = await repo.create({"nombre": data.nombre, "telefono": data.telefono, "activo": True})
    await db.commit()
    profesor = await repo.get_by_id(profesor.id)
    logger.info(f"[PROFESOR_CREADO] nombre={profesor.nombre}")
    return _to_response(profesor)


@router.put("/{profesor_id}", response_model=ProfesorResponse)
async def update_profesor(profesor_id: int, data: ProfesorUpdate, db: AsyncSession = Depends(get_db)):
    repo = ProfesorRepository(db)
    profesor = await repo.get_by_id(profesor_id)
    if not profesor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profesor no encontrado")

    profesor = await repo.update(profesor, data.model_dump(exclude_unset=True))
    await db.commit()
    profesor = await repo.get_by_id(profesor_id)
    logger.info(f"[PROFESOR_ACTUALIZADO] id={profesor_id}")
    return _to_response(profesor)


@router.put("/{profesor_id}/categorias", response_model=ProfesorResponse)
async def asignar_categorias(
    profesor_id: int, data: AsignarCategoriasProfesorRequest, db: AsyncSession = Depends(get_db)
):
    profesor_repo = ProfesorRepository(db)
    profesor = await profesor_repo.get_by_id(profesor_id)
    if not profesor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profesor no encontrado")

    categoria_repo = CategoriaRepository(db)
    categorias = []
    for categoria_id in data.categoria_ids:
        categoria = await categoria_repo.get_by_id(categoria_id)
        if not categoria:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=f"Categoría {categoria_id} no encontrada"
            )
        categorias.append(categoria)

    profesor = await profesor_repo.set_categorias(profesor, categorias)
    await db.commit()
    profesor = await profesor_repo.get_by_id(profesor_id)
    logger.info(f"[PROFESOR_CATEGORIAS_ASIGNADAS] id={profesor_id} categorias={data.categoria_ids}")
    return _to_response(profesor)
