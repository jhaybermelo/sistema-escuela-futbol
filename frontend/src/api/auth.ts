import { api } from './client'
import type { Usuario } from '../types'

export async function login(email: string, password: string): Promise<string> {
  const { data } = await api.post<{ access_token: string; token_type: string }>('/auth/login', {
    email,
    password,
  })
  return data.access_token
}

export async function me(): Promise<Usuario> {
  const { data } = await api.get<Usuario>('/auth/me')
  return data
}

export async function changePassword(password_actual: string, password_nueva: string) {
  await api.post('/auth/change-password', { password_actual, password_nueva })
}
