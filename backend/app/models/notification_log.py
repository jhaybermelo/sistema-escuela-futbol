from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class NotificationLog(Base):
    __tablename__ = "notification_log"
    __table_args__ = (
        UniqueConstraint("mensualidad_id", "tipo", "canal", name="uq_mensualidad_tipo_canal"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    alumno_id: Mapped[int] = mapped_column(ForeignKey("alumnos.id"))
    mensualidad_id: Mapped[int] = mapped_column(ForeignKey("mensualidades.id"))
    tipo: Mapped[str] = mapped_column(String(30))  # previo_vencimiento|vencido
    canal: Mapped[str] = mapped_column(String(20))  # email|whatsapp
    enviado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    exitoso: Mapped[bool] = mapped_column(Boolean)
    detalle_error: Mapped[str | None] = mapped_column(Text, nullable=True)

    alumno = relationship("Alumno")
    mensualidad = relationship("Mensualidad")
