from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.config import settings
from app.core.logging_config import get_logger
from app.database import AsyncSessionLocal
from app.repositories.school_config_repository import SchoolConfigRepository
from app.services.billing_service import BillingService
from app.services.reminder_service import ReminderService

logger = get_logger("scheduler", settings.LOG_DIR)

scheduler = AsyncIOScheduler(timezone=settings.TIMEZONE)


async def run_billing_job():
    """Corre todos los días: genera todas las mensualidades faltantes de cada
    alumno activo (desde su fecha de ingreso o la fecha de inicio de la escuela
    hasta hoy) e idempotentemente omite los periodos que ya existen — así que
    correrlo a diario, sin importar el día de corte, mantiene a todos al día y se
    autorepara solo si el contenedor estuvo caído varios días. Siempre marca como
    vencidas las mensualidades pendientes cuya fecha de vencimiento ya pasó.
    """
    async with AsyncSessionLocal() as db:
        config = await SchoolConfigRepository(db).get()
        await db.commit()
        service = BillingService(db)

        resultado = await service.generar_historial_todos(config)
        logger.info(f"[JOB_FACTURACION] {resultado}")

        vencidas = await service.marcar_vencidas()
        if vencidas:
            logger.info(f"[JOB_MARCAR_VENCIDAS] total={vencidas}")


async def run_reminder_job():
    """Corre todos los días: envía recordatorios de mensualidades próximas a vencer
    y de mensualidades vencidas, evitando reenvíos gracias al NotificationLog."""
    async with AsyncSessionLocal() as db:
        resultado = await ReminderService(db).enviar_recordatorios()
        logger.info(f"[JOB_RECORDATORIOS] {resultado}")


def start_scheduler():
    scheduler.add_job(
        run_billing_job,
        CronTrigger(hour=1, minute=0),
        id="billing_daily_check",
        replace_existing=True,
    )
    scheduler.add_job(
        run_reminder_job,
        CronTrigger(hour=8, minute=0),
        id="reminder_daily",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("[SCHEDULER] iniciado")


def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("[SCHEDULER] detenido")
