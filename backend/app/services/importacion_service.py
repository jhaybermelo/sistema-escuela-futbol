from __future__ import annotations

import csv
import io
import unicodedata
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.date_utils import formatear_periodo
from app.core.logging_config import get_logger
from app.repositories.alumno_repository import AlumnoRepository
from app.repositories.categoria_repository import CategoriaRepository
from app.repositories.mensualidad_repository import MensualidadRepository
from app.repositories.pago_repository import PagoRepository
from app.repositories.school_config_repository import SchoolConfigRepository
from app.schemas.importacion import (
    ImportAlumnoPreview,
    ImportAlumnoRow,
    ImportConfirmResultItem,
    ImportPeriodoPreview,
)
from app.services.billing_service import BillingService
from app.services.categoria_assignment_service import CategoriaAssignmentService

logger = get_logger("importaciones", settings.LOG_DIR)

PREFIJO_NUMERO_PROVISIONAL = "IMP-"

MESES_ES: dict[int, str] = {
    1: "enero", 2: "febrero", 3: "marzo", 4: "abril", 5: "mayo", 6: "junio",
    7: "julio", 8: "agosto", 9: "septiembre", 10: "octubre", 11: "noviembre", 12: "diciembre",
}


def _normalizar(texto: str) -> str:
    """Minúsculas, sin tildes, sin espacios sobrantes — para comparar encabezados de
    CSV exportados desde Excel con variaciones de mayúsculas/acentos."""
    texto = texto.strip().lower()
    return "".join(c for c in unicodedata.normalize("NFD", texto) if unicodedata.category(c) != "Mn")


class ImportacionService:
    """Importación masiva de alumnos desde un CSV heredado (planilla manual de Excel),
    con su historial de mensualidades y pagos ya marcados como 'Pagado' mes a mes.

    Cada columna 'MES X' del CSV se empareja con la Mensualidad cuyo periodo_inicio
    cae en el mes X (mes calendario, verificado contra la planilla real de la
    escuela). Con el dia_corte=1 típico esto equivale a que cada mensualidad sea
    exactamente un mes calendario; si el dia_corte configurado fuera otro, el
    periodo simplemente queda etiquetado por su mes de arranque.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.categoria_repo = CategoriaRepository(db)
        self.alumno_repo = AlumnoRepository(db)
        self.mensualidad_repo = MensualidadRepository(db)
        self.pago_repo = PagoRepository(db)

    @staticmethod
    def _parse_fecha(valor: str) -> date:
        valor = valor.strip()
        for fmt in ("%d/%m/%Y", "%d-%m-%Y"):
            try:
                return datetime.strptime(valor, fmt).date()
            except ValueError:
                continue
        raise ValueError(f"fecha inválida '{valor}' (se espera dd/mm/aaaa)")

    async def siguiente_numero_identificacion(self) -> int:
        """Continúa la numeración provisional 'IMP-NNNN' desde el mayor número ya
        usado en el sistema, en vez de reiniciar cada día — así una segunda
        importación (u otra en el mismo día) no repite números."""
        return await self.alumno_repo.get_max_numero_con_prefijo(PREFIJO_NUMERO_PROVISIONAL) + 1

    def parse_csv(
        self, contenido: bytes, numero_inicial: int = 1
    ) -> tuple[list[ImportAlumnoRow], dict[int, list[str]], dict[int, list[str]]]:
        """Parsea el CSV delimitado por ';'. Devuelve las filas parseables y, por
        separado, errores bloqueantes y advertencias por número de fila (para que un
        dato incompleto no descarte la fila completa: se reporta en la
        previsualización en vez de reventar la importación). Solo van como error
        bloqueante los datos que no se pueden corregir desde la tabla editable de la
        previsualización (fecha inválida); lo demás (acudiente faltante, apellido sin
        separar) es una advertencia que el admin puede completar ahí mismo."""
        try:
            texto = contenido.decode("utf-8-sig")
        except UnicodeDecodeError:
            texto = contenido.decode("latin-1")

        lector = csv.reader(io.StringIO(texto), delimiter=";")
        filas_crudas = [f for f in lector if any(c.strip() for c in f)]
        if not filas_crudas:
            raise ValueError("El archivo CSV está vacío")

        encabezado = filas_crudas[0]
        indices: dict[str, int] = {}
        meses_indices: dict[str, int] = {}
        for i, col in enumerate(encabezado):
            norm = _normalizar(col)
            if norm.startswith("mes "):
                meses_indices[norm.removeprefix("mes ").strip()] = i
            elif "nombre del menor" in norm:
                indices["nombre_menor"] = i
            elif "nombre de padre" in norm or "acudiente" in norm:
                indices["nombre_padre"] = i
            elif "fecha nacimiento" in norm:
                indices["fecha_nacimiento"] = i
            elif norm == "telefono":
                indices["telefono"] = i
            elif "fecha de ingreso" in norm:
                indices["fecha_ingreso"] = i

        requeridas = ["nombre_menor", "fecha_nacimiento", "telefono", "fecha_ingreso"]
        faltantes = [r for r in requeridas if r not in indices]
        if faltantes:
            raise ValueError(f"Faltan columnas requeridas en el CSV: {', '.join(faltantes)}")

        def get(cruda: list[str], clave: str) -> str:
            idx = indices.get(clave)
            if idx is None or idx >= len(cruda):
                return ""
            return cruda[idx].strip()

        filas: list[ImportAlumnoRow] = []
        errores_parseo: dict[int, list[str]] = {}
        advertencias_parseo: dict[int, list[str]] = {}

        for n, cruda in enumerate(filas_crudas[1:], start=1):
            nombre_completo = get(cruda, "nombre_menor")
            if not nombre_completo:
                continue  # fila vacía al final del archivo

            errores: list[str] = []
            advertencias: list[str] = []
            # Nombres siempre en mayúsculas, sin importar cómo vengan en el CSV
            # (ej. "Josué David Narváez Rosas") — mismo criterio que los formularios.
            partes = nombre_completo.upper().split()
            nombres = partes[0] if partes else ""
            apellidos = " ".join(partes[1:]) if len(partes) > 1 else ""
            if not apellidos:
                advertencias.append("No se pudo separar apellido del nombre completo")

            try:
                fecha_nacimiento = self._parse_fecha(get(cruda, "fecha_nacimiento"))
            except ValueError as e:
                errores.append(f"Fecha de nacimiento: {e}")
                fecha_nacimiento = date.today()

            try:
                fecha_ingreso = self._parse_fecha(get(cruda, "fecha_ingreso"))
            except ValueError as e:
                errores.append(f"Fecha de ingreso: {e}")
                fecha_ingreso = date.today()

            nombre_padre = get(cruda, "nombre_padre").upper()
            if not nombre_padre:
                nombre_padre = "Acudiente sin registrar"
                advertencias.append("Falta el nombre del acudiente")

            meses = {mes: (cruda[idx].strip() if idx < len(cruda) else "") for mes, idx in meses_indices.items()}

            filas.append(
                ImportAlumnoRow(
                    fila=n,
                    numero_identificacion=f"{PREFIJO_NUMERO_PROVISIONAL}{numero_inicial + n - 1:04d}",
                    nombres=nombres,
                    apellidos=apellidos,
                    fecha_nacimiento=fecha_nacimiento,
                    fecha_ingreso=fecha_ingreso,
                    acudiente_nombre=nombre_padre,
                    acudiente_telefono=get(cruda, "telefono"),
                    meses=meses,
                )
            )
            if errores:
                errores_parseo[n] = errores
            if advertencias:
                advertencias_parseo[n] = advertencias

        return filas, errores_parseo, advertencias_parseo

    async def preview(
        self,
        filas: list[ImportAlumnoRow],
        errores_parseo: dict[int, list[str]] | None = None,
        advertencias_parseo: dict[int, list[str]] | None = None,
    ) -> list[ImportAlumnoPreview]:
        """Resuelve categoría y simula los periodos de mensualidad de cada fila, sin
        escribir nada en la base de datos (usa los métodos estáticos de cálculo de
        BillingService en memoria)."""
        errores_parseo = errores_parseo or {}
        advertencias_parseo = advertencias_parseo or {}
        config = await SchoolConfigRepository(self.db).get()
        categorias = await self.categoria_repo.list_activas()

        previews: list[ImportAlumnoPreview] = []
        for fila in filas:
            errores = list(errores_parseo.get(fila.fila, []))
            advertencias = list(advertencias_parseo.get(fila.fila, []))

            categoria = next(
                (c for c in categorias if c.anio_nacimiento_min <= fila.fecha_nacimiento.year <= c.anio_nacimiento_max),
                None,
            )
            if categoria is None:
                errores.append(f"Ninguna categoría activa cubre el año de nacimiento {fila.fecha_nacimiento.year}")

            if await self.alumno_repo.get_by_numero_identificacion(fila.numero_identificacion):
                errores.append(f"Ya existe un alumno con el número '{fila.numero_identificacion}'")

            periodos_preview: list[ImportPeriodoPreview] = []
            if categoria is not None:
                fecha_inicio_efectiva = fila.fecha_ingreso
                if config.fecha_inicio and config.fecha_inicio > fecha_inicio_efectiva:
                    fecha_inicio_efectiva = config.fecha_inicio

                hoy = date.today()
                if fecha_inicio_efectiva <= hoy:
                    periodos = BillingService._periodos_en_rango(config.dia_corte, fecha_inicio_efectiva, hoy)
                    for indice, (periodo_inicio, periodo_fin) in enumerate(periodos):
                        if indice == 0 and fecha_inicio_efectiva > periodo_inicio:
                            dias_restantes = BillingService._dias_entrenamiento_en_rango(
                                categoria, fecha_inicio_efectiva, periodo_fin
                            )
                            dias_totales = BillingService._dias_entrenamiento_en_rango(
                                categoria, periodo_inicio, periodo_fin
                            )
                            factor = Decimal(dias_restantes) / Decimal(dias_totales) if dias_totales else Decimal(0)
                            monto = (config.valor_mensualidad * factor).quantize(Decimal("0.01"))
                            prorrateado = True
                        else:
                            monto = config.valor_mensualidad
                            prorrateado = False

                        mes_columna = MESES_ES[periodo_inicio.month]
                        marcado_pagado = fila.meses.get(mes_columna, "").strip().lower() == "pagado"

                        periodos_preview.append(
                            ImportPeriodoPreview(
                                periodo_inicio=periodo_inicio,
                                periodo_fin=periodo_fin,
                                mes_columna=mes_columna,
                                monto=monto,
                                prorrateado=prorrateado,
                                marcado_pagado=marcado_pagado,
                            )
                        )

            previews.append(
                ImportAlumnoPreview(
                    **fila.model_dump(),
                    categoria_nombre=categoria.nombre if categoria else None,
                    periodos=periodos_preview,
                    errores=errores,
                    advertencias=advertencias,
                )
            )
        return previews

    async def confirmar(self, filas: list[ImportAlumnoRow], usuario_id: int) -> list[ImportConfirmResultItem]:
        """Crea cada alumno, su historial de mensualidades y los pagos de los meses
        marcados 'Pagado'. Cada fila se procesa en su propia transacción: si una falla
        (ej. categoría no encontrada, numero_identificacion duplicado), se revierte
        solo esa fila y se continúa con las demás."""
        config_repo = SchoolConfigRepository(self.db)
        resultados: list[ImportConfirmResultItem] = []

        for fila in filas:
            try:
                if await self.alumno_repo.get_by_numero_identificacion(fila.numero_identificacion):
                    raise ValueError(f"Ya existe un alumno con el número '{fila.numero_identificacion}'")

                categoria = await CategoriaAssignmentService(self.db).resolve_categoria(fila.fecha_nacimiento)

                alumno = await self.alumno_repo.create(
                    {
                        "numero_identificacion": fila.numero_identificacion,
                        # .upper() de nuevo aquí (no solo en parse_csv) por si el admin
                        # editó el nombre en la previsualización con minúsculas.
                        "nombres": fila.nombres.strip().upper(),
                        "apellidos": fila.apellidos.strip().upper(),
                        "fecha_nacimiento": fila.fecha_nacimiento,
                        "fecha_ingreso": fila.fecha_ingreso,
                        "acudiente_nombre": fila.acudiente_nombre.strip().upper(),
                        "acudiente_telefono": fila.acudiente_telefono,
                        "categoria_id": categoria.id,
                        "categoria_override": False,
                        "estado": "activo",
                    }
                )
                # Mismo contrato de orden que create_alumno: categoría resuelta y
                # flusheada antes de generar historial (el prorrateo la necesita).
                await self.db.flush()
                await self.db.refresh(alumno, attribute_names=["categoria"])

                config = await config_repo.get()
                generados = await BillingService(self.db).generar_historial_alumno(alumno, config)

                mensualidades = await self.mensualidad_repo.list_by_alumno(alumno.id)
                hoy = date.today()
                pagos_generados = 0
                for mensualidad in mensualidades:
                    mes_columna = MESES_ES[mensualidad.periodo_inicio.month]
                    if fila.meses.get(mes_columna, "").strip().lower() != "pagado":
                        continue

                    periodo_texto = formatear_periodo(mensualidad.periodo_inicio, mensualidad.periodo_fin)
                    await self.pago_repo.create(
                        {
                            "mensualidad_id": mensualidad.id,
                            "monto": mensualidad.monto,
                            "fecha_pago": min(mensualidad.fecha_vencimiento, hoy),
                            "metodo_pago": "efectivo",
                            "recibo_tipo": "generado",
                            "recibo_path": "",
                            "alumno_nombre": f"{alumno.nombres} {alumno.apellidos}",
                            "categoria_nombre": categoria.nombre,
                            "acudiente_nombre": alumno.acudiente_nombre,
                            "acudiente_telefono": alumno.acudiente_telefono,
                            "periodo_texto": periodo_texto,
                            "conceptos": [
                                {
                                    "concepto": "Mensualidad",
                                    "descripcion": f"Mensualidad Escuela de Fútbol - {periodo_texto}",
                                    "monto": str(mensualidad.monto),
                                }
                            ],
                            "registrado_por": usuario_id,
                        }
                    )
                    await self.mensualidad_repo.update(mensualidad, {"estado": "pagado"})
                    pagos_generados += 1

                await self.db.commit()
                logger.info(
                    f"[IMPORT_ALUMNO_CREADO] fila={fila.fila} alumno_id={alumno.id} "
                    f"mensualidades={len(generados)} pagos={pagos_generados}"
                )
                resultados.append(
                    ImportConfirmResultItem(
                        fila=fila.fila,
                        ok=True,
                        alumno_id=alumno.id,
                        mensualidades_generadas=len(generados),
                        pagos_generados=pagos_generados,
                    )
                )
            except Exception as exc:
                await self.db.rollback()
                logger.warning(f"[IMPORT_ALUMNO_ERROR] fila={fila.fila} error={exc}")
                resultados.append(ImportConfirmResultItem(fila=fila.fila, ok=False, error=str(exc)))

        return resultados
