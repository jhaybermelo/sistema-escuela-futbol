from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.profesor import Profesor


class ProfesorRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, profesor_id: int) -> Profesor | None:
        stmt = select(Profesor).options(selectinload(Profesor.categorias)).where(Profesor.id == profesor_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list(self, page: int = 1, size: int = 20) -> tuple[list[Profesor], int]:
        count_stmt = select(func.count()).select_from(Profesor)
        total = (await self.db.execute(count_stmt)).scalar_one()

        stmt = (
            select(Profesor)
            .options(selectinload(Profesor.categorias))
            .order_by(Profesor.nombre)
            .offset((page - 1) * size)
            .limit(size)
        )
        items = (await self.db.execute(stmt)).scalars().all()
        return list(items), total

    async def create(self, data: dict) -> Profesor:
        profesor = Profesor(**data)
        self.db.add(profesor)
        await self.db.flush()
        return profesor

    async def update(self, profesor: Profesor, data: dict) -> Profesor:
        for key, value in data.items():
            setattr(profesor, key, value)
        await self.db.flush()
        return profesor

    async def set_categorias(self, profesor: Profesor, categorias: list) -> Profesor:
        profesor.categorias = categorias
        await self.db.flush()
        return profesor
