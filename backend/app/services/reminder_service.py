from datetime import date, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.logging_config import get_logger
from app.models.alumno import Alumno
from app.models.mensualidad import Mensualidad
from app.repositories.mensualidad_repository import MensualidadRepository
from app.repositories.notification_log_repository import NotificationLogRepository
from app.repositories.school_config_repository import SchoolConfigRepository
from app.services.notification_service import enviar_email, enviar_whatsapp

logger = get_logger("notificaciones", settings.LOG_DIR)


def _mensaje(alumno: Alumno, mensualidad: Mensualidad, tipo: str) -> str:
    if tipo == "bloqueo":
        return (
            f"Hola {alumno.acudiente_nombre}, {alumno.nombres} {alumno.apellidos} tiene mensualidades "
            f"pendientes desde hace varios meses y se cumplió el plazo límite de pago. Por este motivo, "
            f"no se podrá recibir al niño en los entrenamientos hasta que se ponga al día con las "
            f"mensualidades pendientes."
        )
    if tipo == "vencido":
        return (
            f"Hola {alumno.acudiente_nombre}, la mensualidad de {alumno.nombres} {alumno.apellidos} "
            f"correspondiente al periodo {mensualidad.periodo_inicio} - {mensualidad.periodo_fin} "
            f"venció el {mensualidad.fecha_vencimiento} y sigue pendiente de pago."
        )
    return (
        f"Hola {alumno.acudiente_nombre}, te recordamos que la mensualidad de "
        f"{alumno.nombres} {alumno.apellidos} vence el {mensualidad.fecha_vencimiento}."
    )


def _mensaje_bloqueo_profesor(alumno: Alumno) -> str:
    categoria_nombre = alumno.categoria.nombre if alumno.categoria else ""
    return (
        f"Aviso: el alumno {alumno.nombres} {alumno.apellidos} (categoría {categoria_nombre}) no ha "
        f"pagado la mensualidad y no debe ser recibido en el entrenamiento hasta ponerse al día."
    )


class ReminderService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.mensualidad_repo = MensualidadRepository(db)
        self.log_repo = NotificationLogRepository(db)

    async def _procesar(self, mensualidad: Mensualidad, tipo: str) -> tuple[int, int]:
        alumno = mensualidad.alumno
        mensaje = _mensaje(alumno, mensualidad, tipo)
        enviados, fallidos = 0, 0

        if alumno.acudiente_email and not await self.log_repo.existe(mensualidad.id, tipo, "email"):
            try:
                await enviar_email(
                    alumno.acudiente_email,
                    f"Recordatorio de mensualidad - {alumno.nombres} {alumno.apellidos}",
                    mensaje,
                )
                await self.log_repo.create(
                    {
                        "alumno_id": alumno.id,
                        "mensualidad_id": mensualidad.id,
                        "tipo": tipo,
                        "canal": "email",
                        "exitoso": True,
                        "detalle_error": None,
                    }
                )
                enviados += 1
            except Exception as e:  # noqa: BLE001 - se registra el error, no debe interrumpir el job
                await self.log_repo.create(
                    {
                        "alumno_id": alumno.id,
                        "mensualidad_id": mensualidad.id,
                        "tipo": tipo,
                        "canal": "email",
                        "exitoso": False,
                        "detalle_error": str(e)[:500],
                    }
                )
                fallidos += 1
                logger.warning(f"[EMAIL_FALLIDO] mensualidad_id={mensualidad.id} error={e}")

        if alumno.acudiente_telefono and not await self.log_repo.existe(mensualidad.id, tipo, "whatsapp"):
            try:
                await enviar_whatsapp(alumno.acudiente_telefono, mensaje)
                await self.log_repo.create(
                    {
                        "alumno_id": alumno.id,
                        "mensualidad_id": mensualidad.id,
                        "tipo": tipo,
                        "canal": "whatsapp",
                        "exitoso": True,
                        "detalle_error": None,
                    }
                )
                enviados += 1
            except Exception as e:  # noqa: BLE001
                await self.log_repo.create(
                    {
                        "alumno_id": alumno.id,
                        "mensualidad_id": mensualidad.id,
                        "tipo": tipo,
                        "canal": "whatsapp",
                        "exitoso": False,
                        "detalle_error": str(e)[:500],
                    }
                )
                fallidos += 1
                logger.warning(f"[WHATSAPP_FALLIDO] mensualidad_id={mensualidad.id} error={e}")

        return enviados, fallidos

    async def _procesar_bloqueo(self, mensualidad: Mensualidad) -> tuple[int, int]:
        """Avisa al acudiente y a los profesores de la categoría del alumno que se
        cumplió el plazo límite de pago. Se ata a una mensualidad_id concreta (la que
        cruzó el umbral de meses de gracia) para que, igual que 'vencido', el
        UniqueConstraint de NotificationLog impida reenviarlo una vez ya se avisó."""
        alumno = mensualidad.alumno
        enviados, fallidos = 0, 0

        ea, fa = await self._procesar(mensualidad, "bloqueo")
        enviados += ea
        fallidos += fa

        if not await self.log_repo.existe(mensualidad.id, "bloqueo", "whatsapp_profesor"):
            categoria = alumno.categoria
            profesores = [p for p in (categoria.profesores if categoria else []) if p.activo and p.telefono]
            mensaje = _mensaje_bloqueo_profesor(alumno)
            exitoso, detalle_error = False, None
            if not profesores:
                detalle_error = "La categoría no tiene ningún profesor con teléfono registrado"
            else:
                for profesor in profesores:
                    try:
                        await enviar_whatsapp(profesor.telefono, mensaje)
                        exitoso = True
                    except Exception as e:  # noqa: BLE001
                        detalle_error = str(e)[:500]
                        logger.warning(
                            f"[WHATSAPP_PROFESOR_FALLIDO] mensualidad_id={mensualidad.id} "
                            f"profesor_id={profesor.id} error={e}"
                        )

            await self.log_repo.create(
                {
                    "alumno_id": alumno.id,
                    "mensualidad_id": mensualidad.id,
                    "tipo": "bloqueo",
                    "canal": "whatsapp_profesor",
                    "exitoso": exitoso,
                    "detalle_error": None if exitoso else detalle_error,
                }
            )
            if exitoso:
                enviados += 1
            else:
                fallidos += 1

        return enviados, fallidos

    async def enviar_recordatorios(self) -> dict:
        config = await SchoolConfigRepository(self.db).get()
        hoy = date.today()
        fecha_objetivo = hoy + timedelta(days=config.dias_recordatorio_previo)

        por_vencer = await self.mensualidad_repo.list_por_vencer(fecha_objetivo)
        vencidas = await self.mensualidad_repo.list_vencidas()

        revisadas, enviados, fallidos = 0, 0, 0
        for mensualidad in por_vencer:
            revisadas += 1
            e, f = await self._procesar(mensualidad, "previo_vencimiento")
            enviados += e
            fallidos += f
        for mensualidad in vencidas:
            revisadas += 1
            e, f = await self._procesar(mensualidad, "vencido")
            enviados += e
            fallidos += f

        vencidas_por_alumno: dict[int, list[Mensualidad]] = {}
        for mensualidad in vencidas:
            vencidas_por_alumno.setdefault(mensualidad.alumno_id, []).append(mensualidad)

        for lista in vencidas_por_alumno.values():
            lista.sort(key=lambda m: m.periodo_inicio)
            if len(lista) > config.meses_gracia_pago:
                e, f = await self._procesar_bloqueo(lista[config.meses_gracia_pago])
                enviados += e
                fallidos += f

        await self.db.commit()
        logger.info(f"[RECORDATORIOS] revisadas={revisadas} enviados={enviados} fallidos={fallidos}")
        return {"revisadas": revisadas, "enviados": enviados, "fallidos": fallidos}
