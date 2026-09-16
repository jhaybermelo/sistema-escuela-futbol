from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.database import get_db
from app.models.alumno import Alumno
from app.models.categoria import Categoria
from app.models.mensualidad import Mensualidad
from app.models.pago import Pago
from app.models.usuario import Usuario
from app.schemas.dashboard import CategoriaConteo, DashboardResumen

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


def _scope_categorias(usuario: Usuario) -> list[int] | None:
    if usuario.rol == "admin":
        return None
    ids = [c.id for c in usuario.categorias_asignadas]
    return ids or None


@router.get("/resumen", response_model=DashboardResumen)
async def resumen(db: AsyncSession = Depends(get_db), usuario: Usuario = Depends(get_current_user)):
    scope = _scope_categorias(usuario)

    conteo_stmt = (
        select(Categoria.nombre, func.count(Alumno.id))
        .join(Alumno, Alumno.categoria_id == Categoria.id)
        .where(Alumno.estado == "activo")
    )
    if scope is not None:
        conteo_stmt = conteo_stmt.where(Alumno.categoria_id.in_(scope))
    conteo_stmt = conteo_stmt.group_by(Categoria.nombre).order_by(Categoria.nombre)

    filas = (await db.execute(conteo_stmt)).all()
    alumnos_por_categoria = [CategoriaConteo(categoria_nombre=nombre, total=total) for nombre, total in filas]
    alumnos_activos = sum(c.total for c in alumnos_por_categoria)

    if usuario.rol != "admin":
        return DashboardResumen(alumnos_activos=alumnos_activos, alumnos_por_categoria=alumnos_por_categoria)

    hoy = date.today()
    inicio_mes = hoy.replace(day=1)
    ingresos_stmt = select(func.coalesce(func.sum(Pago.monto), 0)).where(Pago.fecha_pago >= inicio_mes)
    ingresos_mes: Decimal = (await db.execute(ingresos_stmt)).scalar_one()

    pendientes_stmt = select(func.count()).select_from(Mensualidad).where(
        Mensualidad.estado.in_(["pendiente", "parcial"])
    )
    mensualidades_pendientes = (await db.execute(pendientes_stmt)).scalar_one()

    vencidas_stmt = select(func.count()).select_from(Mensualidad).where(Mensualidad.estado == "vencido")
    mensualidades_vencidas = (await db.execute(vencidas_stmt)).scalar_one()

    return DashboardResumen(
        alumnos_activos=alumnos_activos,
        alumnos_por_categoria=alumnos_por_categoria,
        ingresos_mes=ingresos_mes,
        mensualidades_pendientes=mensualidades_pendientes,
        mensualidades_vencidas=mensualidades_vencidas,
    )
