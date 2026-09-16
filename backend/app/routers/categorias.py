import math

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, require_admin
from app.core.logging_config import get_logger
from app.config import settings
from app.database import get_db
from app.repositories.categoria_repository import CategoriaRepository
from app.schemas.categoria import (
    CategoriaCreate,
    CategoriaListResponse,
    CategoriaResponse,
    CategoriaUpdate,
)

router = APIRouter(prefix="/categorias", tags=["categorias"])
logger = get_logger("categorias", settings.LOG_DIR)


@router.get("", response_model=CategoriaListResponse, dependencies=[Depends(get_current_user)])
async def list_categorias(page: int = 1, size: int = 50, db: AsyncSession = Depends(get_db)):
    repo = CategoriaRepository(db)
    items, total = await repo.list(page, size)
    return CategoriaListResponse(
        items=items, total=total, page=page, size=size, pages=max(1, math.ceil(total / size))
    )


@router.post(
    "",
    response_model=CategoriaResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_admin)],
)
async def create_categoria(data: CategoriaCreate, db: AsyncSession = Depends(get_db)):
    repo = CategoriaRepository(db)
    if await repo.get_by_nombre(data.nombre):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ya existe una categoría con ese nombre")

    categoria = await repo.create({**data.model_dump(), "activo": True})
    await db.commit()
    await db.refresh(categoria)
    logger.info(f"[CATEGORIA_CREADA] nombre={categoria.nombre}")
    return categoria


@router.get("/{categoria_id}", response_model=CategoriaResponse, dependencies=[Depends(get_current_user)])
async def get_categoria(categoria_id: int, db: AsyncSession = Depends(get_db)):
    repo = CategoriaRepository(db)
    categoria = await repo.get_by_id(categoria_id)
    if not categoria:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Categoría no encontrada")
    return categoria


@router.put("/{categoria_id}", response_model=CategoriaResponse, dependencies=[Depends(require_admin)])
async def update_categoria(categoria_id: int, data: CategoriaUpdate, db: AsyncSession = Depends(get_db)):
    repo = CategoriaRepository(db)
    categoria = await repo.get_by_id(categoria_id)
    if not categoria:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Categoría no encontrada")

    categoria = await repo.update(categoria, data.model_dump(exclude_unset=True))
    await db.commit()
    await db.refresh(categoria)
    logger.info(f"[CATEGORIA_ACTUALIZADA] id={categoria_id}")
    return categoria


@router.delete("/{categoria_id}", dependencies=[Depends(require_admin)])
async def delete_categoria(categoria_id: int, db: AsyncSession = Depends(get_db)):
    repo = CategoriaRepository(db)
    categoria = await repo.get_by_id(categoria_id)
    if not categoria:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Categoría no encontrada")

    await repo.update(categoria, {"activo": False})
    await db.commit()
    logger.info(f"[CATEGORIA_DESACTIVADA] id={categoria_id}")
    return {"detail": "Categoría desactivada"}
