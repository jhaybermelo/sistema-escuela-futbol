import math

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import require_admin
from app.core.logging_config import get_logger
from app.config import settings
from app.core.security import hash_password
from app.database import get_db
from app.models.usuario import Usuario
from app.repositories.categoria_repository import CategoriaRepository
from app.repositories.usuario_repository import UsuarioRepository
from app.schemas.usuario import (
    AsignarCategoriasRequest,
    UsuarioCreate,
    UsuarioListResponse,
    UsuarioResponse,
    UsuarioUpdate,
)

router = APIRouter(prefix="/usuarios", tags=["usuarios"], dependencies=[Depends(require_admin)])
logger = get_logger("usuarios", settings.LOG_DIR)


def _to_response(usuario: Usuario) -> UsuarioResponse:
    return UsuarioResponse(
        id=usuario.id,
        email=usuario.email,
        nombre=usuario.nombre,
        rol=usuario.rol,
        activo=usuario.activo,
        categoria_ids=[c.id for c in usuario.categorias_asignadas],
    )


@router.get("", response_model=UsuarioListResponse)
async def list_usuarios(page: int = 1, size: int = 20, db: AsyncSession = Depends(get_db)):
    repo = UsuarioRepository(db)
    items, total = await repo.list(page, size)
    return UsuarioListResponse(
        items=[_to_response(u) for u in items],
        total=total,
        page=page,
        size=size,
        pages=max(1, math.ceil(total / size)),
    )


@router.post("", response_model=UsuarioResponse, status_code=status.HTTP_201_CREATED)
async def create_usuario(data: UsuarioCreate, db: AsyncSession = Depends(get_db)):
    repo = UsuarioRepository(db)
    if await repo.get_by_email(data.email):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El email ya está registrado")

    usuario = await repo.create(
        {
            "email": data.email,
            "nombre": data.nombre,
            "rol": data.rol,
            "password_hash": hash_password(data.password),
            "activo": True,
        }
    )
    await db.commit()
    usuario = await repo.get_by_id(usuario.id)
    logger.info(f"[USUARIO_CREADO] email={usuario.email} rol={usuario.rol}")
    return _to_response(usuario)


@router.get("/{usuario_id}", response_model=UsuarioResponse)
async def get_usuario(usuario_id: int, db: AsyncSession = Depends(get_db)):
    repo = UsuarioRepository(db)
    usuario = await repo.get_by_id(usuario_id)
    if not usuario:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
    return _to_response(usuario)


@router.put("/{usuario_id}", response_model=UsuarioResponse)
async def update_usuario(usuario_id: int, data: UsuarioUpdate, db: AsyncSession = Depends(get_db)):
    repo = UsuarioRepository(db)
    usuario = await repo.get_by_id(usuario_id)
    if not usuario:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")

    update_data = data.model_dump(exclude_unset=True, exclude={"password"})
    if data.password:
        update_data["password_hash"] = hash_password(data.password)

    usuario = await repo.update(usuario, update_data)
    await db.commit()
    usuario = await repo.get_by_id(usuario_id)
    logger.info(f"[USUARIO_ACTUALIZADO] id={usuario_id}")
    return _to_response(usuario)


@router.put("/{usuario_id}/categorias", response_model=UsuarioResponse)
async def asignar_categorias(
    usuario_id: int, data: AsignarCategoriasRequest, db: AsyncSession = Depends(get_db)
):
    usuario_repo = UsuarioRepository(db)
    usuario = await usuario_repo.get_by_id(usuario_id)
    if not usuario:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
    if usuario.rol != "entrenador":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Solo se pueden asignar categorías a entrenadores"
        )

    categoria_repo = CategoriaRepository(db)
    categorias = []
    for categoria_id in data.categoria_ids:
        categoria = await categoria_repo.get_by_id(categoria_id)
        if not categoria:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=f"Categoría {categoria_id} no encontrada"
            )
        categorias.append(categoria)

    usuario = await usuario_repo.set_categorias(usuario, categorias)
    await db.commit()
    usuario = await usuario_repo.get_by_id(usuario_id)
    logger.info(f"[USUARIO_CATEGORIAS_ASIGNADAS] id={usuario_id} categorias={data.categoria_ids}")
    return _to_response(usuario)
