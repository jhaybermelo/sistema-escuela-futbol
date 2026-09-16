from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.repositories.pago_repository import PagoRepository
from app.schemas.pago import ReciboDataResponse
from app.services.recibo_service import pago_to_recibo_data

router = APIRouter(prefix="/public", tags=["public"])


@router.get("/recibos/{token}", response_model=ReciboDataResponse)
async def get_recibo_publico(token: str, db: AsyncSession = Depends(get_db)):
    """Vista pública del recibo (sin autenticación) para compartir por WhatsApp
    con el acudiente, que no tiene cuenta en el sistema. El token es un UUID no
    adivinable, no una simple secuencia."""
    repo = PagoRepository(db)
    pago = await repo.get_by_token(token)
    if not pago:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recibo no encontrado")

    return pago_to_recibo_data(pago)
