from pydantic import BaseModel, field_validator


class ProfesorBase(BaseModel):
    numero_identificacion: str
    nombre: str
    telefono: str

    @field_validator("nombre")
    @classmethod
    def _a_mayusculas(cls, v: str) -> str:
        return v.strip().upper()

    @field_validator("numero_identificacion")
    @classmethod
    def _limpiar_identificacion(cls, v: str) -> str:
        return v.strip()


class ProfesorCreate(ProfesorBase):
    pass


class ProfesorUpdate(BaseModel):
    numero_identificacion: str | None = None
    nombre: str | None = None
    telefono: str | None = None
    activo: bool | None = None

    @field_validator("nombre")
    @classmethod
    def _a_mayusculas(cls, v: str | None) -> str | None:
        return v.strip().upper() if v is not None else v

    @field_validator("numero_identificacion")
    @classmethod
    def _limpiar_identificacion(cls, v: str | None) -> str | None:
        return v.strip() if v is not None else v


class ProfesorResponse(ProfesorBase):
    id: int
    activo: bool
    categoria_ids: list[int] = []

    model_config = {"from_attributes": True}


class ProfesorListResponse(BaseModel):
    items: list[ProfesorResponse]
    total: int
    page: int
    size: int
    pages: int


class AsignarCategoriasProfesorRequest(BaseModel):
    categoria_ids: list[int]
