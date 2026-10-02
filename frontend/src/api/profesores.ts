import { api } from './client'
import type { ListResponse } from '../types'

export interface Profesor {
  id: number
  numero_identificacion: string
  nombre: string
  telefono: string
  activo: boolean
  categoria_ids: number[]
}

export interface ProfesorCreateInput {
  numero_identificacion: string
  nombre: string
  telefono: string
}

export interface ProfesorUpdateInput {
  numero_identificacion?: string
  nombre?: string
  telefono?: string
  activo?: boolean
}

export async function getProfesores(page = 1, size = 50) {
  const { data } = await api.get<ListResponse<Profesor>>('/profesores', { params: { page, size } })
  return data
}

export async function createProfesor(input: ProfesorCreateInput) {
  const { data } = await api.post<Profesor>('/profesores', input)
  return data
}

export async function updateProfesor(id: number, input: ProfesorUpdateInput) {
  const { data } = await api.put<Profesor>(`/profesores/${id}`, input)
  return data
}

export async function asignarCategorias(id: number, categoriaIds: number[]) {
  const { data } = await api.put<Profesor>(`/profesores/${id}/categorias`, { categoria_ids: categoriaIds })
  return data
}
