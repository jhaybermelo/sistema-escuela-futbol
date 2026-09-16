import { api } from './client'
import type { SchoolConfig } from '../types'

export interface SchoolConfigInput {
  nombre_escuela?: string
  valor_mensualidad?: number
  dia_corte?: number
  dias_recordatorio_previo?: number
  fecha_inicio?: string | null
}

export async function getConfig() {
  const { data } = await api.get<SchoolConfig>('/config')
  return data
}

export async function updateConfig(input: SchoolConfigInput) {
  const { data } = await api.put<SchoolConfig>('/config', input)
  return data
}
