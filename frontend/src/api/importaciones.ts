import { api } from './client'
import type { ImportAlumnoPreview, ImportAlumnoRow, ImportConfirmResultItem } from '../types'

export async function previewImportAlumnos(file: File) {
  const formData = new FormData()
  formData.append('file', file)
  const { data } = await api.post<{ filas: ImportAlumnoPreview[] }>('/importaciones/alumnos/preview', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return data.filas
}

export async function confirmarImportAlumnos(filas: ImportAlumnoRow[]) {
  const { data } = await api.post<{ resultados: ImportConfirmResultItem[] }>('/importaciones/alumnos/confirmar', {
    filas,
  })
  return data.resultados
}
