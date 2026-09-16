import { api } from './client'
import type { EstadoMensualidad, ListResponse, Mensualidad, ResumenAlumno } from '../types'

export async function getMensualidades(params: {
  page?: number
  size?: number
  alumno_id?: number
  estado?: EstadoMensualidad
  categoria_id?: number
  search?: string
}) {
  const { data } = await api.get<ListResponse<Mensualidad>>('/mensualidades', { params })
  return data
}

export async function getResumenAlumno(alumnoId: number) {
  const { data } = await api.get<ResumenAlumno>(`/mensualidades/alumno/${alumnoId}/resumen`)
  return data
}

export interface ResumenCarteraItem {
  pendientes: number
  vencidas: number
}

export async function getResumenCartera() {
  const { data } = await api.get<{ por_alumno: Record<number, ResumenCarteraItem> }>(
    '/mensualidades/resumen-cartera',
  )
  return data.por_alumno
}

export async function generarPeriodo() {
  const { data } = await api.post<{ alumnos_revisados: number; mensualidades_generadas: number }>(
    '/mensualidades/generar-periodo',
  )
  return data
}

export async function marcarPagado(id: number) {
  const { data } = await api.post<Mensualidad>(`/mensualidades/${id}/marcar-pagado`)
  return data
}

export async function marcarPendiente(id: number) {
  const { data } = await api.post<Mensualidad>(`/mensualidades/${id}/marcar-pendiente`)
  return data
}
