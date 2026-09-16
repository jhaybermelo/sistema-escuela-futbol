import calendar
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging_config import get_logger
from app.config import settings
from app.models.alumno import Alumno
from app.models.categoria import Categoria
from app.models.school_config import SchoolConfig
from app.repositories.alumno_repository import AlumnoRepository
from app.repositories.mensualidad_repository import MensualidadRepository

logger = get_logger("facturacion", settings.LOG_DIR)


class BillingService:
    """Motor de facturación: cálculo de periodos, prorrateo de ingreso a mitad de
    ciclo, y generación de las mensualidades mensuales de toda la escuela."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.mensualidad_repo = MensualidadRepository(db)
        self.alumno_repo = AlumnoRepository(db)

    @staticmethod
    def _periodo_actual(dia_corte: int, hoy: date) -> tuple[date, date]:
        """Devuelve (periodo_inicio, periodo_fin) del ciclo mensual que contiene `hoy`,
        dado un día de corte fijo (1-28) para toda la escuela.

        periodo_inicio = el último día de corte en/antes de `hoy`.
        periodo_fin = el día anterior al siguiente día de corte.
        """
        dia_corte = min(dia_corte, calendar.monthrange(hoy.year, hoy.month)[1])
        if hoy.day >= dia_corte:
            periodo_inicio = date(hoy.year, hoy.month, dia_corte)
        else:
            mes_anterior = hoy.month - 1 or 12
            anio_mes_anterior = hoy.year - 1 if hoy.month == 1 else hoy.year
            dia_valido = min(dia_corte, calendar.monthrange(anio_mes_anterior, mes_anterior)[1])
            periodo_inicio = date(anio_mes_anterior, mes_anterior, dia_valido)

        siguiente_mes = periodo_inicio.month + 1 if periodo_inicio.month < 12 else 1
        anio_siguiente = periodo_inicio.year + 1 if periodo_inicio.month == 12 else periodo_inicio.year
        dia_siguiente_valido = min(dia_corte, calendar.monthrange(anio_siguiente, siguiente_mes)[1])
        siguiente_corte = date(anio_siguiente, siguiente_mes, dia_siguiente_valido)
        periodo_fin = siguiente_corte - timedelta(days=1)

        return periodo_inicio, periodo_fin

    @staticmethod
    def _dias_entrenamiento_en_rango(categoria: Categoria, inicio: date, fin: date) -> int:
        """Cuenta cuántos días de entrenamiento de la categoría (0=lunes..6=domingo)
        caen dentro del rango [inicio, fin], ambos inclusive."""
        if inicio > fin or not categoria.dias_entrenamiento:
            return 0
        dias_set = set(categoria.dias_entrenamiento)
        total = 0
        cursor = inicio
        while cursor <= fin:
            if cursor.weekday() in dias_set:
                total += 1
            cursor += timedelta(days=1)
        return total

    @staticmethod
    def _periodos_en_rango(dia_corte: int, desde: date, hasta: date) -> list[tuple[date, date]]:
        """Lista de (periodo_inicio, periodo_fin) que cubren desde el periodo que
        contiene `desde` hasta el periodo que contiene `hasta`, en orden cronológico."""
        if desde > hasta:
            return []
        periodos = []
        periodo_inicio, periodo_fin = BillingService._periodo_actual(dia_corte, desde)
        while periodo_inicio <= hasta:
            periodos.append((periodo_inicio, periodo_fin))
            periodo_inicio, periodo_fin = BillingService._periodo_actual(dia_corte, periodo_fin + timedelta(days=1))
        return periodos

    async def generar_historial_alumno(
        self, alumno: Alumno, config: SchoolConfig, hasta: date | None = None
    ) -> list[dict]:
        """Genera todas las mensualidades faltantes de un alumno, desde el más tardío
        entre la fecha de inicio de la escuela y su fecha de ingreso, hasta `hasta`
        (por defecto hoy). Solo el primer periodo se prorratea si el punto de partida
        cae a mitad de ciclo; el resto se factura completo. Idempotente: los periodos
        que ya tienen mensualidad se omiten.

        Requiere que `alumno.categoria` ya esté cargada/asignada antes de llamarse.
        """
        hoy = date.today()
        hasta = hasta or hoy
        fecha_inicio_efectiva = alumno.fecha_ingreso
        if config.fecha_inicio and config.fecha_inicio > fecha_inicio_efectiva:
            fecha_inicio_efectiva = config.fecha_inicio

        if fecha_inicio_efectiva > hasta:
            return []

        periodos = self._periodos_en_rango(config.dia_corte, fecha_inicio_efectiva, hasta)
        generados = []

        for indice, (periodo_inicio, periodo_fin) in enumerate(periodos):
            existente = await self.mensualidad_repo.get_by_alumno_periodo(alumno.id, periodo_inicio)
            if existente:
                continue

            if indice == 0 and fecha_inicio_efectiva > periodo_inicio:
                categoria = alumno.categoria
                dias_restantes = self._dias_entrenamiento_en_rango(
                    categoria, fecha_inicio_efectiva, periodo_fin
                )
                dias_totales = self._dias_entrenamiento_en_rango(categoria, periodo_inicio, periodo_fin)
                factor = Decimal(dias_restantes) / Decimal(dias_totales) if dias_totales else Decimal(0)
                monto = (config.valor_mensualidad * factor).quantize(Decimal("0.01"))
                prorrateado = True
            else:
                monto = config.valor_mensualidad
                prorrateado = False

            estado = "vencido" if periodo_fin < hoy else "pendiente"

            mensualidad = await self.mensualidad_repo.create(
                {
                    "alumno_id": alumno.id,
                    "periodo_inicio": periodo_inicio,
                    "periodo_fin": periodo_fin,
                    "monto": monto,
                    "monto_prorrateado": prorrateado,
                    "estado": estado,
                    "fecha_vencimiento": periodo_fin,
                }
            )
            generados.append({"mensualidad_id": mensualidad.id, "monto": monto, "prorrateado": prorrateado})

        if generados:
            logger.info(f"[HISTORIAL_GENERADO] alumno_id={alumno.id} periodos={len(generados)}")
        return generados

    async def generar_historial_todos(self, config: SchoolConfig) -> dict:
        """Genera, para cada alumno activo, todas las mensualidades faltantes desde
        su punto de partida (fecha de inicio de la escuela o su fecha de ingreso, la
        que sea más tardía) hasta hoy — no solo el periodo actual. Idempotente: los
        periodos que ya tienen mensualidad se omiten, así que puede llamarse tantas
        veces como se quiera (botón manual "Generar periodo actual" o el job diario
        del scheduler) sin duplicar cargos."""
        alumnos = await self.alumno_repo.list_activos()

        total_generadas = 0
        for alumno in alumnos:
            generados = await self.generar_historial_alumno(alumno, config)
            total_generadas += len(generados)

        await self.db.commit()
        logger.info(f"[GENERAR_HISTORIAL_TODOS] alumnos={len(alumnos)} mensualidades={total_generadas}")
        return {"alumnos_revisados": len(alumnos), "mensualidades_generadas": total_generadas}

    async def marcar_vencidas(self, hoy: date | None = None) -> int:
        hoy = hoy or date.today()
        pendientes = await self.mensualidad_repo.list_pendientes_vencidas(hoy)
        for mensualidad in pendientes:
            mensualidad.estado = "vencido"
        await self.db.commit()
        if pendientes:
            logger.info(f"[MARCAR_VENCIDAS] total={len(pendientes)}")
        return len(pendientes)
