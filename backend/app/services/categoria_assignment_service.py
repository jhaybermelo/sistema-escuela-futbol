from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.categoria import Categoria
from app.repositories.alumno_repository import AlumnoRepository
from app.repositories.categoria_repository import CategoriaRepository


class CategoriaAssignmentService:
    """Resuelve automáticamente la categoría de un alumno según su año de nacimiento."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.categoria_repo = CategoriaRepository(db)
        self.alumno_repo = AlumnoRepository(db)

    async def resolve_categoria(self, fecha_nacimiento: date) -> Categoria:
        anio = fecha_nacimiento.year
        categorias = await self.categoria_repo.list_activas()
        match = next(
            (c for c in categorias if c.anio_nacimiento_min <= anio <= c.anio_nacimiento_max), None
        )
        if not match:
            raise ValueError(f"Ninguna categoría activa cubre el año de nacimiento {anio}")
        return match

    async def recompute_all(self) -> list[dict]:
        """Recalcula la categoría de todos los alumnos sin asignación manual (categoria_override=False).

        Devuelve la lista de cambios aplicados, cada uno con nombres de categoría antes/después.
        """
        alumnos = await self.alumno_repo.list_sin_override()
        cambios = []
        for alumno in alumnos:
            try:
                nueva_categoria = await self.resolve_categoria(alumno.fecha_nacimiento)
            except ValueError:
                continue
            if nueva_categoria.id != alumno.categoria_id:
                categoria_anterior_nombre = alumno.categoria.nombre if alumno.categoria else "—"
                cambios.append(
                    {
                        "alumno_id": alumno.id,
                        "alumno_nombre": f"{alumno.nombres} {alumno.apellidos}",
                        "categoria_anterior": categoria_anterior_nombre,
                        "categoria_nueva": nueva_categoria.nombre,
                    }
                )
                alumno.categoria_id = nueva_categoria.id
        await self.db.flush()
        return cambios
