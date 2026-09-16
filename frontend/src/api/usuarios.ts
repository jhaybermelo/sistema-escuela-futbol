import { api } from './client'
import type { ListResponse, Rol } from '../types'

export interface Usuario {
  id: number
  email: string
  nombre: string
  rol: Rol
  activo: boolean
  categoria_ids: number[]
}

export interface UsuarioCreateInput {
  email: string
  nombre: string
  rol: Rol
  password: string
}

export interface UsuarioUpdateInput {
  email?: string
  nombre?: string
  rol?: Rol
  activo?: boolean
  password?: string
}

export async function getUsuarios(page = 1, size = 20) {
  const { data } = await api.get<ListResponse<Usuario>>('/usuarios', { params: { page, size } })
  return data
}

export async function createUsuario(input: UsuarioCreateInput) {
  const { data } = await api.post<Usuario>('/usuarios', input)
  return data
}

export async function updateUsuario(id: number, input: UsuarioUpdateInput) {
  const { data } = await api.put<Usuario>(`/usuarios/${id}`, input)
  return data
}

export async function asignarCategorias(id: number, categoriaIds: number[]) {
  const { data } = await api.put<Usuario>(`/usuarios/${id}/categorias`, { categoria_ids: categoriaIds })
  return data
}
