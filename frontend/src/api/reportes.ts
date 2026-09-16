import { api } from './client'

export interface MetodoPagoResumen {
  metodo_pago: string
  total: string
  cantidad: number
}

export interface PagoReporteItem {
  id: number
  fecha_pago: string
  alumno_nombre: string
  periodo_texto: string
  metodo_pago: string
  monto: string
}

export interface ReportePagosResponse {
  mes: number
  anio: number
  total_general: string
  cantidad_total: number
  por_metodo: MetodoPagoResumen[]
  pagos: PagoReporteItem[]
}

export async function getReportePagos(mes: number, anio: number) {
  const { data } = await api.get<ReportePagosResponse>('/reportes/pagos', { params: { mes, anio } })
  return data
}
