import { useRef, useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import toast from 'react-hot-toast'
import { Upload, CheckCircle2, XCircle, AlertTriangle } from 'lucide-react'
import * as importacionesApi from '../api/importaciones'
import { Button } from '../components/ui/Button'
import { Input } from '../components/ui/Input'
import { getErrorMessage } from '../lib/errors'
import type { ImportAlumnoPreview, ImportConfirmResultItem } from '../types'

function toRowInput(fila: ImportAlumnoPreview) {
  return {
    fila: fila.fila,
    numero_identificacion: fila.numero_identificacion,
    nombres: fila.nombres,
    apellidos: fila.apellidos,
    fecha_nacimiento: fila.fecha_nacimiento,
    fecha_ingreso: fila.fecha_ingreso,
    acudiente_nombre: fila.acudiente_nombre,
    acudiente_telefono: fila.acudiente_telefono,
    meses: fila.meses,
  }
}

export default function AlumnoImportPage() {
  const inputRef = useRef<HTMLInputElement>(null)
  const [filas, setFilas] = useState<ImportAlumnoPreview[]>([])
  const [resultados, setResultados] = useState<ImportConfirmResultItem[]>([])

  const previewMutation = useMutation({
    mutationFn: importacionesApi.previewImportAlumnos,
    onSuccess: (data) => {
      setFilas(data)
      setResultados([])
    },
    onError: (err) => toast.error(getErrorMessage(err, 'Error al leer el CSV')),
  })

  const confirmarMutation = useMutation({
    mutationFn: importacionesApi.confirmarImportAlumnos,
    onSuccess: (data) => {
      setResultados(data)
      const exitosos = data.filter((r) => r.ok).length
      toast.success(`${exitosos} de ${data.length} alumno(s) importados correctamente`)
    },
    onError: (err) => toast.error(getErrorMessage(err, 'Error al confirmar la importación')),
  })

  function recalcularEstado(fila: ImportAlumnoPreview): ImportAlumnoPreview {
    // Al editar un campo en la previsualización, se descartan las advertencias/errores
    // de ese campo que ya no aplican con el valor corregido — de lo contrario quedan
    // "pegados" desde el parseo inicial del CSV y el botón de confirmar nunca se habilita.
    const advertencias = fila.advertencias.filter((a) => {
      if (a === 'Falta el nombre del acudiente') {
        return !fila.acudiente_nombre.trim() || fila.acudiente_nombre === 'Acudiente sin registrar'
      }
      if (a === 'No se pudo separar apellido del nombre completo') {
        return !fila.apellidos.trim()
      }
      return true
    })
    const errores = fila.errores.filter((e) => {
      if (e.startsWith('Ya existe un alumno con el número')) return false
      return true
    })
    return { ...fila, advertencias, errores }
  }

  function actualizarFila(fila: number, campo: keyof ImportAlumnoPreview, valor: string) {
    setFilas((prev) => prev.map((f) => (f.fila === fila ? recalcularEstado({ ...f, [campo]: valor }) : f)))
  }

  const hayErroresBloqueantes = filas.some((f) => f.errores.length > 0)
  const resultadoPorFila = new Map(resultados.map((r) => [r.fila, r]))

  return (
    <div>
      <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold text-slate-800">Importar alumnos desde CSV</h1>
          <p className="mt-1 text-sm text-slate-500">
            Sube el CSV con columnas <code>Nombre del menor</code>, <code>Nombre de Padre</code>,{' '}
            <code>fecha Nacimiento</code>, <code>TELEFONO</code>, <code>FECHA DE INGRESO</code> y una columna{' '}
            <code>MES &lt;nombre&gt;</code> por cada mes (valores <code>Pagado</code> / <code>Debe</code> / vacío).
            Los pagos se registran en efectivo, con recibo generado.
          </p>
        </div>
        <div>
          <input
            ref={inputRef}
            type="file"
            accept=".csv"
            className="hidden"
            onChange={(e) => {
              const file = e.target.files?.[0]
              if (file) previewMutation.mutate(file)
              e.target.value = ''
            }}
          />
          <Button className="gap-2" onClick={() => inputRef.current?.click()} disabled={previewMutation.isPending}>
            <Upload size={16} /> {previewMutation.isPending ? 'Leyendo...' : 'Seleccionar CSV'}
          </Button>
        </div>
      </div>

      {filas.length > 0 && (
        <>
          <div className="mb-4 flex flex-wrap items-center justify-between gap-3 rounded-md bg-slate-50 p-3 text-sm text-slate-600">
            <span>
              {filas.length} fila(s) leídas.{' '}
              {hayErroresBloqueantes
                ? 'Corrige las filas en rojo antes de confirmar.'
                : 'Revisa los datos y confirma para crear los alumnos.'}
            </span>
            <Button
              onClick={() => confirmarMutation.mutate(filas.map(toRowInput))}
              disabled={hayErroresBloqueantes || confirmarMutation.isPending}
            >
              {confirmarMutation.isPending ? 'Importando...' : 'Confirmar importación'}
            </Button>
          </div>

          <div className="space-y-4">
            {filas.map((fila) => {
              const resultado = resultadoPorFila.get(fila.fila)
              return (
                <div
                  key={fila.fila}
                  className={`rounded-lg border bg-white p-4 ${
                    fila.errores.length > 0 ? 'border-red-300' : 'border-slate-200'
                  }`}
                >
                  <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
                    <span className="text-xs font-medium uppercase text-slate-400">Fila {fila.fila}</span>
                    {resultado && (
                      <span
                        className={`flex items-center gap-1 rounded-full px-2 py-1 text-xs font-medium ${
                          resultado.ok ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-700'
                        }`}
                      >
                        {resultado.ok ? <CheckCircle2 size={14} /> : <XCircle size={14} />}
                        {resultado.ok
                          ? `Creado (${resultado.pagos_generados} recibo(s))`
                          : resultado.error}
                      </span>
                    )}
                  </div>

                  <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
                    <Input
                      label="Identificación"
                      value={fila.numero_identificacion}
                      onChange={(e) => actualizarFila(fila.fila, 'numero_identificacion', e.target.value)}
                    />
                    <Input
                      label="Nombres"
                      className="uppercase"
                      value={fila.nombres}
                      onChange={(e) => actualizarFila(fila.fila, 'nombres', e.target.value)}
                    />
                    <Input
                      label="Apellidos"
                      className="uppercase"
                      value={fila.apellidos}
                      onChange={(e) => actualizarFila(fila.fila, 'apellidos', e.target.value)}
                    />
                    <div className="flex flex-col gap-1">
                      <span className="text-sm font-medium text-slate-700">Categoría</span>
                      <span className="rounded-md border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-600">
                        {fila.categoria_nombre ?? '—'}
                      </span>
                    </div>
                    <Input
                      label="Acudiente"
                      className="uppercase"
                      value={fila.acudiente_nombre}
                      onChange={(e) => actualizarFila(fila.fila, 'acudiente_nombre', e.target.value)}
                    />
                    <Input
                      label="Teléfono acudiente"
                      value={fila.acudiente_telefono}
                      onChange={(e) => actualizarFila(fila.fila, 'acudiente_telefono', e.target.value)}
                    />
                    <Input label="Fecha de nacimiento" value={fila.fecha_nacimiento} readOnly />
                    <Input label="Fecha de ingreso" value={fila.fecha_ingreso} readOnly />
                  </div>

                  {fila.periodos.length > 0 && (
                    <div className="mt-3 flex flex-wrap gap-2">
                      {fila.periodos.map((p) => (
                        <span
                          key={p.periodo_inicio}
                          className={`rounded-full px-2 py-1 text-xs font-medium ${
                            p.marcado_pagado ? 'bg-green-100 text-green-800' : 'bg-slate-100 text-slate-600'
                          }`}
                          title={`${p.periodo_inicio} a ${p.periodo_fin}${p.prorrateado ? ' (prorrateado)' : ''}`}
                        >
                          {p.mes_columna}: ${p.monto} {p.marcado_pagado ? 'Pagado' : 'Pendiente'}
                        </span>
                      ))}
                    </div>
                  )}

                  {(fila.errores.length > 0 || fila.advertencias.length > 0) && (
                    <ul className="mt-3 space-y-1 text-xs">
                      {fila.errores.map((e, i) => (
                        <li key={`e-${i}`} className="flex items-center gap-1 text-red-600">
                          <XCircle size={12} /> {e}
                        </li>
                      ))}
                      {fila.advertencias.map((a, i) => (
                        <li key={`a-${i}`} className="flex items-center gap-1 text-amber-600">
                          <AlertTriangle size={12} /> {a}
                        </li>
                      ))}
                    </ul>
                  )}

                  {resultado?.ok && resultado.alumno_id && (
                    <div className="mt-3">
                      <Link to={`/alumnos/${resultado.alumno_id}`} className="text-xs text-green-700 hover:underline">
                        Ver alumno creado →
                      </Link>
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        </>
      )}
    </div>
  )
}
