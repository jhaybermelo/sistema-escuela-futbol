import { api } from './client'
import type { CanalNotificacion, ListResponse, NotificationLog, TipoNotificacion } from '../types'

export async function getNotificaciones(params: {
  page?: number
  size?: number
  tipo?: TipoNotificacion
  canal?: CanalNotificacion
  exitoso?: boolean
}) {
  const { data } = await api.get<ListResponse<NotificationLog>>('/notificaciones', { params })
  return data
}

export async function enviarRecordatorios() {
  const { data } = await api.post<{ revisadas: number; enviados: number; fallidos: number }>(
    '/notificaciones/enviar-recordatorios',
  )
  return data
}
