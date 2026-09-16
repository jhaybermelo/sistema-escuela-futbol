import { api } from './client'
import type { Alumno, EstadoAlumno, ListResponse } from '../types'

export interface AlumnoInput {
  numero_identificacion: string
  nombres: string
  apellidos: string
  fecha_nacimiento: string
  fecha_ingreso: string
  acudiente_nombre: string
  acudiente_telefono: string
  acudiente_email?: string | null
  categoria_id?: number | null
}

export async function getAlumnos(params: {
  page?: number
  size?: number
  search?: string
  categoria_id?: number
  estado?: EstadoAlumno
}) {
  const { data } = await api.get<ListResponse<Alumno>>('/alumnos', { params })
  return data
}

export async function getAlumno(id: number) {
  const { data } = await api.get<Alumno>(`/alumnos/${id}`)
  return data
}

export async function createAlumno(input: AlumnoInput) {
  const { data } = await api.post<Alumno>('/alumnos', input)
  return data
}

export async function updateAlumno(id: number, input: Partial<AlumnoInput> & { estado?: EstadoAlumno }) {
  const { data } = await api.put<Alumno>(`/alumnos/${id}`, input)
  return data
}

export async function uploadFoto(id: number, file: File) {
  const formData = new FormData()
  formData.append('file', file)
  const { data } = await api.post<Alumno>(`/alumnos/${id}/foto`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return data
}

export async function recomputeCategorias() {
  const { data } = await api.post<{
    actualizados: { alumno_id: number; alumno_nombre: string; categoria_anterior: string; categoria_nueva: string }[]
    total_revisados: number
  }>('/alumnos/recompute-categorias')
  return data
}

export async function generarHistorial() {
  const { data } = await api.post<{ alumnos_revisados: number; mensualidades_generadas: number }>(
    '/alumnos/generar-historial',
  )
  return data
}

export async function getCarnetBlob(id: number, formato: 'png' | 'pdf') {
  const { data } = await api.get<Blob>(`/alumnos/${id}/carnet`, {
    params: { formato },
    responseType: 'blob',
  })
  return data
}
