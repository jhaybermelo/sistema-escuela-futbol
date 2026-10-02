from pydantic import BaseModel, EmailStr, Field, field_validator


class UsuarioBase(BaseModel):
    email: EmailStr
    nombre: str
    rol: str = Field(pattern="^(admin|entrenador)$")

    @field_validator("nombre")
    @classmethod
    def _a_mayusculas(cls, v: str) -> str:
        return v.strip().upper()


class UsuarioCreate(UsuarioBase):
    password: str = Field(min_length=6)


class UsuarioUpdate(BaseModel):
    email: EmailStr | None = None
    nombre: str | None = None
    rol: str | None = Field(default=None, pattern="^(admin|entrenador)$")
    activo: bool | None = None
    password: str | None = Field(default=None, min_length=6)

    @field_validator("nombre")
    @classmethod
    def _a_mayusculas(cls, v: str | None) -> str | None:
        return v.strip().upper() if v is not None else v


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
