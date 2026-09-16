from email.message import EmailMessage

import aiosmtplib
import httpx

from app.config import settings
from app.core.logging_config import get_logger

logger = get_logger("notificaciones", settings.LOG_DIR)


async def enviar_email(destinatario: str, asunto: str, cuerpo: str) -> None:
    if not settings.SMTP_HOST or not settings.SMTP_USER:
        raise RuntimeError("SMTP no configurado (SMTP_HOST/SMTP_USER faltantes)")

    mensaje = EmailMessage()
    mensaje["From"] = settings.SMTP_FROM or settings.SMTP_USER
    mensaje["To"] = destinatario
    mensaje["Subject"] = asunto
    mensaje.set_content(cuerpo)

    await aiosmtplib.send(
        mensaje,
        hostname=settings.SMTP_HOST,
        port=settings.SMTP_PORT,
        username=settings.SMTP_USER,
        password=settings.SMTP_PASSWORD,
        start_tls=True,
    )


async def enviar_whatsapp(telefono: str, mensaje: str) -> None:
    """Envía un mensaje de WhatsApp usando la API gratuita de CallMeBot.

    El número debe haber activado previamente el bot de CallMeBot (enviándole
    "I allow callmebot to send me messages" por WhatsApp) para poder recibir mensajes.
    """
    if not settings.CALLMEBOT_API_KEY:
        raise RuntimeError("CallMeBot no configurado (CALLMEBOT_API_KEY faltante)")

    params = {
        "phone": telefono,
        "text": mensaje,
        "apikey": settings.CALLMEBOT_API_KEY,
    }
    async with httpx.AsyncClient(timeout=15) as client:
        response = await client.get("https://api.callmebot.com/whatsapp.php", params=params)
        response.raise_for_status()
