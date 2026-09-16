import { api } from './client'
import type { ListResponse } from '../types'

export interface Pago {
  id: number
  mensualidad_id: number
  monto: string
  fecha_pago: string
  metodo_pago: string
  recibo_tipo: 'generado' | 'subido'
  recibo_path: string
  referencia: string | null
  observaciones: string | null
  created_at: string
}

export interface PagoInput {
  mensualidad_id: number
  monto: number
  fecha_pago: string
  metodo_pago: string
  recibo_tipo: 'generado' | 'subido'
  referencia?: string
  observaciones?: string
  file?: File
}

export interface ReciboConcepto {
  concepto: string
  descripcion: string
  monto: string
}

export interface ReciboData {
  numero_recibo: string
  fecha: string
  alumno_nombre: string
  categoria_nombre: string
  acudiente_nombre: string
  acudiente_telefono: string
  periodo_texto: string
  metodo_pago: string
  referencia: string | null
  observaciones: string | null
  conceptos: ReciboConcepto[]
  total: string
}

export async function getPagos(params: { page?: number; size?: number; mensualidad_id?: number }) {
  const { data } = await api.get<ListResponse<Pago>>('/pagos', { params })
  return data
}

export async function createPago(input: PagoInput) {
  const formData = new FormData()
  formData.append('mensualidad_id', String(input.mensualidad_id))
  formData.append('monto', String(input.monto))
  formData.append('fecha_pago', input.fecha_pago)
  formData.append('metodo_pago', input.metodo_pago)
  formData.append('recibo_tipo', input.recibo_tipo)
  if (input.referencia) formData.append('referencia', input.referencia)
  if (input.observaciones) formData.append('observaciones', input.observaciones)
  if (input.file) formData.append('file', input.file)

  const { data } = await api.post<Pago>('/pagos', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return data
}

export async function getReciboData(pagoId: number) {
  const { data } = await api.get<ReciboData>(`/pagos/${pagoId}/recibo-data`)
  return data
}
