from datetime import date
from decimal import Decimal

from sqlalchemy import Date, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class SchoolConfig(Base):
    """Configuración global de la escuela. Fila única (id=1)."""

    __tablename__ = "school_config"

    id: Mapped[int] = mapped_column(primary_key=True)
    nombre_escuela: Mapped[str] = mapped_column(String(150), default="Escuela de Futbol")
    valor_mensualidad: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)
    dia_corte: Mapped[int] = mapped_column(Integer, default=1)  # 1-28
    dias_recordatorio_previo: Mapped[int] = mapped_column(Integer, default=3)
    # Fecha desde la que la escuela lleva historial de mensualidades. Al crear o
    # backfillear un alumno, el histórico nunca arranca antes de esta fecha aunque
    # su fecha_ingreso sea anterior.
    fecha_inicio: Mapped[date | None] = mapped_column(Date, nullable=True)
