from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Alumno(Base):
    __tablename__ = "alumnos"

    id: Mapped[int] = mapped_column(primary_key=True)
    numero_identificacion: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    nombres: Mapped[str] = mapped_column(String(150))
    apellidos: Mapped[str] = mapped_column(String(150))
    fecha_nacimiento: Mapped[date] = mapped_column(Date)
    fecha_ingreso: Mapped[date] = mapped_column(Date)
    foto_path: Mapped[str | None] = mapped_column(String(255), nullable=True)

    categoria_id: Mapped[int] = mapped_column(ForeignKey("categorias.id"))
    categoria_override: Mapped[bool] = mapped_column(Boolean, default=False)

    acudiente_nombre: Mapped[str] = mapped_column(String(150))
    acudiente_telefono: Mapped[str] = mapped_column(String(30))
    acudiente_email: Mapped[str | None] = mapped_column(String(255), nullable=True)

    estado: Mapped[str] = mapped_column(String(20), default="activo")  # activo|inactivo|retirado

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    categoria = relationship("Categoria")
