from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.core.logging_config import get_logger
from app.core.security import create_access_token, verify_password, hash_password
from app.config import settings
from app.database import get_db
from app.models.usuario import Usuario
from app.repositories.usuario_repository import UsuarioRepository
from app.schemas.auth import ChangePasswordRequest, LoginRequest, TokenResponse
from app.schemas.usuario import UsuarioResponse

router = APIRouter(prefix="/auth", tags=["auth"])
logger = get_logger("auth", settings.LOG_DIR)


@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    repo = UsuarioRepository(db)
    usuario = await repo.get_by_email(data.email)
    if not usuario or not usuario.activo or not verify_password(data.password, usuario.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales inválidas")

    token = create_access_token({"sub": str(usuario.id), "rol": usuario.rol})
    logger.info(f"[LOGIN] usuario={usuario.email}")
    return TokenResponse(access_token=token)


@router.get("/me", response_model=UsuarioResponse)
async def me(usuario: Usuario = Depends(get_current_user)):
    return UsuarioResponse(
        id=usuario.id,
        email=usuario.email,
        nombre=usuario.nombre,
        rol=usuario.rol,
        activo=usuario.activo,
        categoria_ids=[c.id for c in usuario.categorias_asignadas],
    )


@router.post("/change-password")
async def change_password(
    data: ChangePasswordRequest,
    usuario: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not verify_password(data.password_actual, usuario.password_hash):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Contraseña actual incorrecta")

    repo = UsuarioRepository(db)
    await repo.update(usuario, {"password_hash": hash_password(data.password_nueva)})
    await db.commit()
    logger.info(f"[CHANGE_PASSWORD] usuario={usuario.email}")
    return {"detail": "Contraseña actualizada"}
