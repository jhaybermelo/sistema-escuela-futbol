import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Pago(Base):
    __tablename__ = "pagos"

    id: Mapped[int] = mapped_column(primary_key=True)
    mensualidad_id: Mapped[int] = mapped_column(ForeignKey("mensualidades.id"))
    monto: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    fecha_pago: Mapped[date] = mapped_column(Date)
    metodo_pago: Mapped[str] = mapped_column(String(30))  # efectivo|transferencia|nequi|otro
    recibo_tipo: Mapped[str] = mapped_column(String(20))  # generado|subido|historico
    recibo_path: Mapped[str] = mapped_column(String(255))
    referencia: Mapped[str | None] = mapped_column(String(100), nullable=True)
    observaciones: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Token público (no adivinable) para compartir el recibo por WhatsApp sin
    # necesitar que el acudiente tenga una cuenta en el sistema.
    token: Mapped[str] = mapped_column(String(36), unique=True, default=lambda: str(uuid.uuid4()))

    # Foto de los datos del alumno/mensualidad al momento del pago, para que el
    # recibo oficial nunca cambie retroactivamente si luego se edita el alumno.
    alumno_nombre: Mapped[str] = mapped_column(String(300), default="")
    categoria_nombre: Mapped[str] = mapped_column(String(100), default="")
    acudiente_nombre: Mapped[str] = mapped_column(String(150), default="")
    acudiente_telefono: Mapped[str] = mapped_column(String(30), default="")
    periodo_texto: Mapped[str] = mapped_column(String(100), default="")
    conceptos: Mapped[list[dict]] = mapped_column(JSONB, default=list)

    registrado_por: Mapped[int] = mapped_column(ForeignKey("usuarios.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    mensualidad = relationship("Mensualidad", back_populates="pagos")
