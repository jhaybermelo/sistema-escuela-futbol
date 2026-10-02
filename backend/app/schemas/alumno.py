from datetime import date

from pydantic import BaseModel, EmailStr, Field, field_validator


class AlumnoBase(BaseModel):
    numero_identificacion: str
    nombres: str
    apellidos: str
    fecha_nacimiento: date
    fecha_ingreso: date
    acudiente_nombre: str
    acudiente_telefono: str
    acudiente_email: EmailStr | None = None

    # Los nombres siempre se guardan en mayúsculas, sin importar cómo se escriban en
    # el formulario o en un CSV importado — mantiene consistente el listado, el
    # carnet y los recibos sin depender de que cada punto de entrada lo normalice.
    @field_validator("nombres", "apellidos", "acudiente_nombre")
    @classmethod
    def _a_mayusculas(cls, v: str) -> str:
        return v.strip().upper()


class AlumnoCreate(AlumnoBase):
    categoria_id: int | None = None  # si se especifica, se marca como asignación manual (override)


class AlumnoUpdate(BaseModel):
    numero_identificacion: str | None = None
    nombres: str | None = None
    apellidos: str | None = None
    fecha_nacimiento: date | None = None
    fecha_ingreso: date | None = None
    acudiente_nombre: str | None = None
    acudiente_telefono: str | None = None
    acudiente_email: EmailStr | None = None
    categoria_id: int | None = None
    estado: str | None = Field(default=None, pattern="^(activo|inactivo|retirado)$")

    @field_validator("nombres", "apellidos", "acudiente_nombre")
    @classmethod
    def _a_mayusculas(cls, v: str | None) -> str | None:
        return v.strip().upper() if v is not None else v


class AlumnoResponse(AlumnoBase):
    id: int
    categoria_id: int
    categoria_nombre: str
    categoria_override: bool
    foto_path: str | None
    estado: str

    model_config = {"from_attributes": True}


class AlumnoListResponse(BaseModel):
    items: list[AlumnoResponse]
    total: int
    page: int
    size: int
    pages: int


class RecomputeResultItem(BaseModel):
    alumno_id: int
    alumno_nombre: str
    categoria_anterior: str
    categoria_nueva: str


class RecomputeResult(BaseModel):
    actualizados: list[RecomputeResultItem]
    total_revisados: int


class GenerarHistorialResult(BaseModel):
    alumnos_revisados: int
    mensualidades_generadas: int
