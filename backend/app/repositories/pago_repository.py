from __future__ import annotations

from decimal import Decimal

from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.pago import Pago


class PagoRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, pago_id: int) -> Pago | None:
        stmt = select(Pago).options(selectinload(Pago.mensualidad)).where(Pago.id == pago_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_token(self, token: str) -> Pago | None:
        stmt = select(Pago).where(Pago.token == token)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list(
        self, page: int = 1, size: int = 20, mensualidad_id: int | None = None
    ) -> tuple[list[Pago], int]:
        conditions = []
        if mensualidad_id:
            conditions.append(Pago.mensualidad_id == mensualidad_id)

        count_stmt = select(func.count()).select_from(Pago)
        list_stmt = select(Pago).options(selectinload(Pago.mensualidad))
        for cond in conditions:
            count_stmt = count_stmt.where(cond)
            list_stmt = list_stmt.where(cond)

        total = (await self.db.execute(count_stmt)).scalar_one()
        list_stmt = list_stmt.order_by(Pago.fecha_pago.desc()).offset((page - 1) * size).limit(size)
        items = (await self.db.execute(list_stmt)).scalars().all()
        return list(items), total

    async def total_pagado(self, mensualidad_id: int) -> Decimal:
        stmt = select(func.coalesce(func.sum(Pago.monto), 0)).where(Pago.mensualidad_id == mensualidad_id)
        result = await self.db.execute(stmt)
        return result.scalar_one()

    async def create(self, data: dict) -> Pago:
        pago = Pago(**data)
        self.db.add(pago)
        await self.db.flush()
        return pago

    async def update(self, pago: Pago, data: dict) -> Pago:
        for key, value in data.items():
            setattr(pago, key, value)
        await self.db.flush()
        return pago

    async def delete_historicos(self, mensualidad_id: int) -> None:
        """Elimina los pagos registrados vía el marcado rápido histórico (sin recibo
        real) para una mensualidad, usado al deshacer un 'marcar como pagado'."""
        stmt = delete(Pago).where(Pago.mensualidad_id == mensualidad_id, Pago.recibo_tipo == "historico")
        await self.db.execute(stmt)
        await self.db.flush()
