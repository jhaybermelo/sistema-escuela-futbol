from __future__ import annotations

from datetime import date

from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.alumno import Alumno
from app.models.mensualidad import Mensualidad


class MensualidadRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, mensualidad_id: int) -> Mensualidad | None:
        stmt = (
            select(Mensualidad)
            .options(
                selectinload(Mensualidad.alumno).selectinload(Alumno.categoria),
                selectinload(Mensualidad.pagos),
            )
            .where(Mensualidad.id == mensualidad_id)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_alumno_periodo(self, alumno_id: int, periodo_inicio: date) -> Mensualidad | None:
        stmt = select(Mensualidad).where(
            Mensualidad.alumno_id == alumno_id, Mensualidad.periodo_inicio == periodo_inicio
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list(
        self,
        page: int = 1,
        size: int = 20,
        alumno_id: int | None = None,
        estado: str | None = None,
        categoria_id: int | None = None,
        search: str | None = None,
    ) -> tuple[list[Mensualidad], int]:
        conditions = []
        if alumno_id:
            conditions.append(Mensualidad.alumno_id == alumno_id)
        if estado:
            conditions.append(Mensualidad.estado == estado)
        if categoria_id:
            conditions.append(Alumno.categoria_id == categoria_id)
        if search:
            like = f"%{search}%"
            conditions.append(or_(Alumno.nombres.ilike(like), Alumno.apellidos.ilike(like)))

        needs_join = categoria_id is not None or search is not None

        count_stmt = select(func.count()).select_from(Mensualidad)
        list_stmt = select(Mensualidad).options(
            selectinload(Mensualidad.alumno), selectinload(Mensualidad.pagos)
        )
        if needs_join:
            count_stmt = count_stmt.join(Alumno, Mensualidad.alumno_id == Alumno.id)
            list_stmt = list_stmt.join(Alumno, Mensualidad.alumno_id == Alumno.id)
        for cond in conditions:
            count_stmt = count_stmt.where(cond)
            list_stmt = list_stmt.where(cond)

        total = (await self.db.execute(count_stmt)).scalar_one()
        list_stmt = (
            list_stmt.order_by(Mensualidad.periodo_inicio.desc()).offset((page - 1) * size).limit(size)
        )
        items = (await self.db.execute(list_stmt)).scalars().all()
        return list(items), total

    async def list_pendientes_vencidas(self, hoy: date) -> list[Mensualidad]:
        stmt = select(Mensualidad).where(
            Mensualidad.estado.in_(["pendiente", "parcial"]), Mensualidad.fecha_vencimiento < hoy
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def list_por_vencer(self, fecha_objetivo: date) -> list[Mensualidad]:
        stmt = (
            select(Mensualidad)
            .options(selectinload(Mensualidad.alumno))
            .where(
                Mensualidad.estado.in_(["pendiente", "parcial"]),
                Mensualidad.fecha_vencimiento == fecha_objetivo,
            )
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def list_vencidas(self) -> list[Mensualidad]:
        stmt = (
            select(Mensualidad)
            .options(selectinload(Mensualidad.alumno))
            .where(Mensualidad.estado == "vencido")
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def resumen_cartera(self) -> dict[int, dict]:
        """Conteo de pendientes/vencidas por alumno, para todos los alumnos con al
        menos una mensualidad, en una sola consulta (evita N+1 en la lista de
        alumnos)."""
        stmt = select(Mensualidad.alumno_id, Mensualidad.estado, func.count()).group_by(
            Mensualidad.alumno_id, Mensualidad.estado
        )
        result = await self.db.execute(stmt)
        resumen: dict[int, dict] = {}
        for alumno_id, estado, total in result.all():
            conteo = resumen.setdefault(alumno_id, {"pendientes": 0, "vencidas": 0})
            if estado in ("pendiente", "parcial"):
                conteo["pendientes"] += total
            elif estado == "vencido":
                conteo["vencidas"] += total
        return resumen

    async def resumen_por_alumno(self, alumno_id: int) -> dict:
        stmt = select(Mensualidad.estado, func.count()).where(Mensualidad.alumno_id == alumno_id).group_by(
            Mensualidad.estado
        )
        result = await self.db.execute(stmt)
        conteos = dict(result.all())
        return {
            "total_mensualidades": sum(conteos.values()),
            "pagadas": conteos.get("pagado", 0),
            "pendientes": conteos.get("pendiente", 0) + conteos.get("parcial", 0),
            "vencidas": conteos.get("vencido", 0),
        }

    async def create(self, data: dict) -> Mensualidad:
        mensualidad = Mensualidad(**data)
        self.db.add(mensualidad)
        await self.db.flush()
        return mensualidad

    async def update(self, mensualidad: Mensualidad, data: dict) -> Mensualidad:
        for key, value in data.items():
            setattr(mensualidad, key, value)
        await self.db.flush()
        return mensualidad
