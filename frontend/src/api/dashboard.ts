import { api } from './client'

export interface CategoriaConteo {
  categoria_nombre: string
  total: number
}

export interface DashboardResumen {
  alumnos_activos: number
  alumnos_por_categoria: CategoriaConteo[]
  ingresos_mes: string | null
  mensualidades_pendientes: number | null
  mensualidades_vencidas: number | null
}

export async function getResumen() {
  const { data } = await api.get<DashboardResumen>('/dashboard/resumen')
  return data
}
