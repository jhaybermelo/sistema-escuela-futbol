from pydantic import BaseModel, EmailStr, Field


class UsuarioBase(BaseModel):
    email: EmailStr
    nombre: str
    rol: str = Field(pattern="^(admin|entrenador)$")


class UsuarioCreate(UsuarioBase):
    password: str = Field(min_length=6)


class UsuarioUpdate(BaseModel):
    email: EmailStr | None = None
    nombre: str | None = None
    rol: str | None = Field(default=None, pattern="^(admin|entrenador)$")
    activo: bool | None = None
    password: str | None = Field(default=None, min_length=6)


class UsuarioResponse(UsuarioBase):
    id: int
    activo: bool
    categoria_ids: list[int] = []

    model_config = {"from_attributes": True}


class UsuarioListResponse(BaseModel):
    items: list[UsuarioResponse]
    total: int
    page: int
    size: int
    pages: int


class AsignarCategoriasRequest(BaseModel):
    categoria_ids: list[int]
