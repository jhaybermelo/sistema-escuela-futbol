from app.models.pago import Pago
from app.schemas.pago import ReciboDataResponse


def pago_to_recibo_data(pago: Pago) -> ReciboDataResponse:
    return ReciboDataResponse(
        numero_recibo=f"{pago.id:04d}",
        token=pago.token,
        fecha=pago.fecha_pago,
        alumno_nombre=pago.alumno_nombre,
        categoria_nombre=pago.categoria_nombre,
        acudiente_nombre=pago.acudiente_nombre,
        acudiente_telefono=pago.acudiente_telefono,
        periodo_texto=pago.periodo_texto,
        metodo_pago=pago.metodo_pago,
        referencia=pago.referencia,
        observaciones=pago.observaciones,
        conceptos=pago.conceptos,
        total=pago.monto,
    )
