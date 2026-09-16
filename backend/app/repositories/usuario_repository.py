from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.usuario import Usuario


class UsuarioRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, usuario_id: int) -> Usuario | None:
        stmt = (
            select(Usuario)
            .options(selectinload(Usuario.categorias_asignadas))
            .where(Usuario.id == usuario_id)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Usuario | None:
        result = await self.db.execute(select(Usuario).where(Usuario.email == email))
        return result.scalar_one_or_none()

    async def list(self, page: int = 1, size: int = 20) -> tuple[list[Usuario], int]:
        count_stmt = select(func.count()).select_from(Usuario)
        total = (await self.db.execute(count_stmt)).scalar_one()

        stmt = (
            select(Usuario)
            .options(selectinload(Usuario.categorias_asignadas))
            .order_by(Usuario.nombre)
            .offset((page - 1) * size)
            .limit(size)
        )
        items = (await self.db.execute(stmt)).scalars().all()
        return list(items), total

    async def create(self, data: dict) -> Usuario:
        usuario = Usuario(**data)
        self.db.add(usuario)
        await self.db.flush()
        return usuario

    async def update(self, usuario: Usuario, data: dict) -> Usuario:
        for key, value in data.items():
            setattr(usuario, key, value)
        await self.db.flush()
        return usuario

    async def set_categorias(self, usuario: Usuario, categorias: list) -> Usuario:
        usuario.categorias_asignadas = categorias
        await self.db.flush()
        return usuario
