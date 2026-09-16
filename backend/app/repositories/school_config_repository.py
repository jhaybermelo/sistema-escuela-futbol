from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.school_config import SchoolConfig


class SchoolConfigRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get(self) -> SchoolConfig:
        result = await self.db.execute(select(SchoolConfig).where(SchoolConfig.id == 1))
        config = result.scalar_one_or_none()
        if config is None:
            config = SchoolConfig(id=1)
            self.db.add(config)
            await self.db.flush()
        return config

    async def update(self, config: SchoolConfig, data: dict) -> SchoolConfig:
        for key, value in data.items():
            setattr(config, key, value)
        await self.db.flush()
        return config
