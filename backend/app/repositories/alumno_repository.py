from __future__ import annotations

from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.alumno import Alumno


class AlumnoRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, alumno_id: int) -> Alumno | None:
        stmt = select(Alumno).options(selectinload(Alumno.categoria)).where(Alumno.id == alumno_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_numero_identificacion(self, numero: str) -> Alumno | None:
        result = await self.db.execute(
            select(Alumno).where(Alumno.numero_identificacion == numero)
        )
        return result.scalar_one_or_none()

    async def list(
        self,
        page: int = 1,
        size: int = 20,
        search: str | None = None,
        categoria_id: int | None = None,
        estado: str | None = None,
        categoria_ids_scope: list[int] | None = None,
    ) -> tuple[list[Alumno], int]:
        conditions = []
        if search:
            like = f"%{search}%"
            conditions.append(
                or_(
                    Alumno.nombres.ilike(like),
                    Alumno.apellidos.ilike(like),
                    Alumno.numero_identificacion.ilike(like),
                )
            )
        if categoria_id:
            conditions.append(Alumno.categoria_id == categoria_id)
        if estado:
            conditions.append(Alumno.estado == estado)
        if categoria_ids_scope is not None:
            conditions.append(Alumno.categoria_id.in_(categoria_ids_scope))

        count_stmt = select(func.count()).select_from(Alumno)
        list_stmt = select(Alumno).options(selectinload(Alumno.categoria))
        for cond in conditions:
            count_stmt = count_stmt.where(cond)
            list_stmt = list_stmt.where(cond)

        total = (await self.db.execute(count_stmt)).scalar_one()
        list_stmt = list_stmt.order_by(Alumno.apellidos, Alumno.nombres).offset((page - 1) * size).limit(size)
        items = (await self.db.execute(list_stmt)).scalars().all()
        return list(items), total

    async def list_activos(self) -> list[Alumno]:
        stmt = (
            select(Alumno)
            .options(selectinload(Alumno.categoria))
            .where(Alumno.estado == "activo")
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def list_sin_override(self) -> list[Alumno]:
        stmt = (
            select(Alumno)
            .options(selectinload(Alumno.categoria))
            .where(Alumno.categoria_override.is_(False))
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def create(self, data: dict) -> Alumno:
        alumno = Alumno(**data)
        self.db.add(alumno)
        await self.db.flush()
        return alumno

    async def update(self, alumno: Alumno, data: dict) -> Alumno:
        for key, value in data.items():
            setattr(alumno, key, value)
        await self.db.flush()
        return alumno
