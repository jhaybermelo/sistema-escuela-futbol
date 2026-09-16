from __future__ import annotations

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.notification_log import NotificationLog


class NotificationLogRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def existe(self, mensualidad_id: int, tipo: str, canal: str) -> bool:
        stmt = select(NotificationLog.id).where(
            NotificationLog.mensualidad_id == mensualidad_id,
            NotificationLog.tipo == tipo,
            NotificationLog.canal == canal,
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def list(
        self,
        page: int = 1,
        size: int = 20,
        alumno_id: int | None = None,
        tipo: str | None = None,
        canal: str | None = None,
        exitoso: bool | None = None,
    ) -> tuple[list[NotificationLog], int]:
        conditions = []
        if alumno_id:
            conditions.append(NotificationLog.alumno_id == alumno_id)
        if tipo:
            conditions.append(NotificationLog.tipo == tipo)
        if canal:
            conditions.append(NotificationLog.canal == canal)
        if exitoso is not None:
            conditions.append(NotificationLog.exitoso == exitoso)

        count_stmt = select(func.count()).select_from(NotificationLog)
        list_stmt = select(NotificationLog).options(selectinload(NotificationLog.alumno))
        for cond in conditions:
            count_stmt = count_stmt.where(cond)
            list_stmt = list_stmt.where(cond)

        total = (await self.db.execute(count_stmt)).scalar_one()
        list_stmt = list_stmt.order_by(NotificationLog.enviado_en.desc()).offset((page - 1) * size).limit(size)
        items = (await self.db.execute(list_stmt)).scalars().all()
        return list(items), total

    async def create(self, data: dict) -> NotificationLog:
        registro = NotificationLog(**data)
        self.db.add(registro)
        await self.db.flush()
        return registro
