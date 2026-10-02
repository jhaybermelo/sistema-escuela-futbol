from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.alumno import Alumno
from app.models.categoria import Categoria


class CategoriaRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def conteo_alumnos_activos(self) -> dict[int, int]:
        """Cantidad de alumnos activos por categoria_id, en una sola consulta (evita
        N+1 al listar categorías)."""
        stmt = (
            select(Alumno.categoria_id, func.count())
            .where(Alumno.estado == "activo")
            .group_by(Alumno.categoria_id)
        )
        result = await self.db.execute(stmt)
        return dict(result.all())

    async def get_by_id(self, categoria_id: int) -> Categoria | None:
        stmt = (
            select(Categoria)
            .options(selectinload(Categoria.profesores))
            .where(Categoria.id == categoria_id)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_nombre(self, nombre: str) -> Categoria | None:
        result = await self.db.execute(select(Categoria).where(Categoria.nombre == nombre))
        return result.scalar_one_or_none()

    async def list_activas(self) -> list[Categoria]:
        result = await self.db.execute(
            select(Categoria).where(Categoria.activo.is_(True)).order_by(Categoria.anio_nacimiento_min)
        )
        return list(result.scalars().all())

    async def list(self, page: int = 1, size: int = 20) -> tuple[list[Categoria], int]:
        total = (await self.db.execute(select(func.count()).select_from(Categoria))).scalar_one()
        stmt = (
            select(Categoria)
            .order_by(Categoria.anio_nacimiento_min)
            .offset((page - 1) * size)
            .limit(size)
        )
        items = (await self.db.execute(stmt)).scalars().all()
        return list(items), total

    async def create(self, data: dict) -> Categoria:
        categoria = Categoria(**data)
        self.db.add(categoria)
        await self.db.flush()
        return categoria

    async def update(self, categoria: Categoria, data: dict) -> Categoria:
        for key, value in data.items():
            setattr(categoria, key, value)
        await self.db.flush()
        return categoria
