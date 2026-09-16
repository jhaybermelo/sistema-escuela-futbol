from pydantic import BaseModel, Field, field_validator


class CategoriaBase(BaseModel):
    nombre: str
    anio_nacimiento_min: int
    anio_nacimiento_max: int
    dias_entrenamiento: list[int] = Field(default_factory=list)

    @field_validator("dias_entrenamiento")
    @classmethod
    def validar_dias(cls, v: list[int]) -> list[int]:
        if any(d < 0 or d > 6 for d in v):
            raise ValueError("Los días de entrenamiento deben estar entre 0 (lunes) y 6 (domingo)")
        return sorted(set(v))

    @field_validator("anio_nacimiento_max")
    @classmethod
    def validar_rango(cls, v: int, info) -> int:
        minimo = info.data.get("anio_nacimiento_min")
        if minimo is not None and v < minimo:
            raise ValueError("anio_nacimiento_max debe ser mayor o igual a anio_nacimiento_min")
        return v


class CategoriaCreate(CategoriaBase):
    pass


class CategoriaUpdate(BaseModel):
    nombre: str | None = None
    anio_nacimiento_min: int | None = None
    anio_nacimiento_max: int | None = None
    dias_entrenamiento: list[int] | None = None
    activo: bool | None = None


class CategoriaResponse(CategoriaBase):
    id: int
    activo: bool

    model_config = {"from_attributes": True}


class CategoriaListResponse(BaseModel):
    items: list[CategoriaResponse]
    total: int
    page: int
    size: int
    pages: int
