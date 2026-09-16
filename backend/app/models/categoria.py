from sqlalchemy import Boolean, String, Table, Column, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

entrenador_categoria = Table(
    "entrenador_categoria",
    Base.metadata,
    Column("usuario_id", ForeignKey("usuarios.id", ondelete="CASCADE"), primary_key=True),
    Column("categoria_id", ForeignKey("categorias.id", ondelete="CASCADE"), primary_key=True),
)


class Categoria(Base):
    __tablename__ = "categorias"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(100), unique=True)
    anio_nacimiento_min: Mapped[int] = mapped_column(Integer)
    anio_nacimiento_max: Mapped[int] = mapped_column(Integer)
    # Días de entrenamiento por semana: 0=lunes ... 6=domingo (date.weekday())
    dias_entrenamiento: Mapped[list[int]] = mapped_column(ARRAY(Integer), default=list)
    activo: Mapped[bool] = mapped_column(Boolean, default=True)

    entrenadores = relationship(
        "Usuario", secondary=entrenador_categoria, back_populates="categorias_asignadas"
    )
