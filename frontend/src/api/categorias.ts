import { api } from './client'
import type { Categoria, ListResponse } from '../types'

export interface CategoriaInput {
  nombre: string
  anio_nacimiento_min: number
  anio_nacimiento_max: number
  dias_entrenamiento: number[]
}

export async function getCategorias(page = 1, size = 50) {
  const { data } = await api.get<ListResponse<Categoria>>('/categorias', { params: { page, size } })
  return data
}

export async function createCategoria(input: CategoriaInput) {
  const { data } = await api.post<Categoria>('/categorias', input)
  return data
}

export async function updateCategoria(id: number, input: Partial<CategoriaInput> & { activo?: boolean }) {
  const { data } = await api.put<Categoria>(`/categorias/${id}`, input)
  return data
}

export async function deleteCategoria(id: number) {
  await api.delete(`/categorias/${id}`)
}
