from pydantic import BaseModel


class ProfesorBase(BaseModel):
    nombre: str
    telefono: str


class ProfesorCreate(ProfesorBase):
    pass


class ProfesorUpdate(BaseModel):
    nombre: str | None = None
    telefono: str | None = None
    activo: bool | None = None


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
