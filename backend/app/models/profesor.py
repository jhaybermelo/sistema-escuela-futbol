from sqlalchemy import Boolean, String, Table, Column, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

profesor_categoria = Table(
    "profesor_categoria",
    Base.metadata,
    Column("profesor_id", ForeignKey("profesores.id", ondelete="CASCADE"), primary_key=True),
    Column("categoria_id", ForeignKey("categorias.id", ondelete="CASCADE"), primary_key=True),
)


class Profesor(Base):
    """Profesor de una o varias categorías, solo para recibir el aviso de WhatsApp de
    alumnos en mora — no tiene cuenta de acceso al sistema (a diferencia de un
    Usuario con rol 'entrenador')."""

    __tablename__ = "profesores"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String(150))
    telefono: Mapped[str] = mapped_column(String(30))
    activo: Mapped[bool] = mapped_column(Boolean, default=True)

    categorias = relationship("Categoria", secondary=profesor_categoria, back_populates="profesores")
