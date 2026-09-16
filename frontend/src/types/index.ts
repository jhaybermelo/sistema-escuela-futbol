export type Rol = 'admin' | 'entrenador'

export interface Usuario {
  id: number
  email: string
  nombre: string
  rol: Rol
  activo: boolean
}

export interface Categoria {
  id: number
  nombre: string
  anio_nacimiento_min: number
  anio_nacimiento_max: number
  dias_entrenamiento: number[]
  activo: boolean
}

export type EstadoAlumno = 'activo' | 'inactivo' | 'retirado'

export interface Alumno {
  id: number
  numero_identificacion: string
  nombres: string
  apellidos: string
  fecha_nacimiento: string
  fecha_ingreso: string
  acudiente_nombre: string
  acudiente_telefono: string
  acudiente_email: string | null
  categoria_id: number
  categoria_nombre: string
  categoria_override: boolean
  foto_path: string | null
  estado: EstadoAlumno
}

export interface SchoolConfig {
  nombre_escuela: string
  valor_mensualidad: string
  dia_corte: number
  dias_recordatorio_previo: number
  fecha_inicio: string | null
}

export type EstadoMensualidad = 'pendiente' | 'parcial' | 'pagado' | 'vencido'

export interface Mensualidad {
  id: number
  alumno_id: number
  alumno_nombre: string
  periodo_inicio: string
  periodo_fin: string
  monto: string
  monto_prorrateado: boolean
  estado: EstadoMensualidad
  fecha_vencimiento: string
  total_pagado: string
}

export interface ResumenAlumno {
  alumno_id: number
  total_mensualidades: number
  pagadas: number
  pendientes: number
  vencidas: number
  meses_desde_inicio_escuela: number | null
}

export type TipoNotificacion = 'previo_vencimiento' | 'vencido'
export type CanalNotificacion = 'email' | 'whatsapp'

export interface NotificationLog {
  id: number
  alumno_id: number
  alumno_nombre: string
  mensualidad_id: number
  tipo: TipoNotificacion
  canal: CanalNotificacion
  enviado_en: string
  exitoso: boolean
  detalle_error: string | null
}

export interface ListResponse<T> {
  items: T[]
  total: number
  page: number
  size: number
  pages: number
}
