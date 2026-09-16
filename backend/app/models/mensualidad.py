from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Numeric, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Mensualidad(Base):
    __tablename__ = "mensualidades"
    __table_args__ = (UniqueConstraint("alumno_id", "periodo_inicio", name="uq_alumno_periodo"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    alumno_id: Mapped[int] = mapped_column(ForeignKey("alumnos.id"))
    periodo_inicio: Mapped[date] = mapped_column(Date)
    periodo_fin: Mapped[date] = mapped_column(Date)
    monto: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    monto_prorrateado: Mapped[bool] = mapped_column(Boolean, default=False)
    estado: Mapped[str] = mapped_column(String(20), default="pendiente")  # pendiente|parcial|pagado|vencido
    fecha_vencimiento: Mapped[date] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    alumno = relationship("Alumno")
    pagos = relationship("Pago", back_populates="mensualidad", order_by="Pago.fecha_pago")
