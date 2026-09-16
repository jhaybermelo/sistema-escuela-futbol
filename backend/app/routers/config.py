from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import require_admin
from app.core.logging_config import get_logger
from app.config import settings
from app.database import get_db
from app.repositories.school_config_repository import SchoolConfigRepository
from app.schemas.school_config import SchoolConfigResponse, SchoolConfigUpdate

router = APIRouter(prefix="/config", tags=["config"], dependencies=[Depends(require_admin)])
logger = get_logger("config", settings.LOG_DIR)


@router.get("", response_model=SchoolConfigResponse)
async def get_config(db: AsyncSession = Depends(get_db)):
    repo = SchoolConfigRepository(db)
    config = await repo.get()
    await db.commit()
    return config


@router.put("", response_model=SchoolConfigResponse)
async def update_config(data: SchoolConfigUpdate, db: AsyncSession = Depends(get_db)):
    repo = SchoolConfigRepository(db)
    config = await repo.get()
    config = await repo.update(config, data.model_dump(exclude_unset=True))
    await db.commit()
    await db.refresh(config)
    logger.info(f"[CONFIG_ACTUALIZADA] valor_mensualidad={config.valor_mensualidad} dia_corte={config.dia_corte}")
    return config
