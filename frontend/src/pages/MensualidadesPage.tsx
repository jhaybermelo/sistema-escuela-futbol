import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link, useSearchParams } from 'react-router-dom'
import toast from 'react-hot-toast'
import { RefreshCw, X, Receipt, CheckCircle2, Undo2, Search } from 'lucide-react'
import * as mensualidadesApi from '../api/mensualidades'
import * as pagosApi from '../api/pagos'
import * as categoriasApi from '../api/categorias'
import type { EstadoMensualidad, Mensualidad } from '../types'
import { Button } from '../components/ui/Button'
import { Input } from '../components/ui/Input'
import { Pagination } from '../components/ui/Pagination'
import { PagoFormModal } from '../components/PagoFormModal'
import { getErrorMessage } from '../lib/errors'

const ESTADO_COLOR: Record<EstadoMensualidad, string> = {
  pendiente: 'bg-amber-100 text-amber-800',
  parcial: 'bg-blue-100 text-blue-800',
  pagado: 'bg-green-100 text-green-800',
  vencido: 'bg-red-100 text-red-700',
}

const ESTADO_LABEL: Record<EstadoMensualidad, string> = {
  pendiente: 'Pendiente',
  parcial: 'Parcial',
  pagado: 'Pagado',
  vencido: 'Vencido',
}

export default function MensualidadesPage() {
  const queryClient = useQueryClient()
  const [searchParams, setSearchParams] = useSearchParams()
  const alumnoId = searchParams.get('alumno_id')
  const [page, setPage] = useState(1)
  const [estado, setEstado] = useState<EstadoMensualidad | ''>('')
  const [categoriaId, setCategoriaId] = useState('')
  const [search, setSearch] = useState('')
  const [pagoModalFor, setPagoModalFor] = useState<Mensualidad | null>(null)
  const [pagosDe, setPagosDe] = useState<number | null>(null)

  const { data, isLoading } = useQuery({
    queryKey: ['mensualidades', page, estado, categoriaId, search, alumnoId],
    queryFn: () =>
      mensualidadesApi.getMensualidades({
        page,
        size: 20,
        estado: estado || undefined,
        categoria_id: categoriaId ? Number(categoriaId) : undefined,
        search: search || undefined,
        alumno_id: alumnoId ? Number(alumnoId) : undefined,
      }),
  })

  const { data: categorias } = useQuery({
    queryKey: ['categorias'],
    queryFn: () => categoriasApi.getCategorias(),
  })

  const generarMutation = useMutation({
    mutationFn: mensualidadesApi.generarPeriodo,
    onSuccess: (result) => {
      queryClient.invalidateQueries({ queryKey: ['mensualidades'] })
      toast.success(
        `${result.mensualidades_generadas} mensualidad(es) generadas en ${result.alumnos_revisados} alumno(s) revisados`,
      )
    },
    onError: (err) => toast.error(getErrorMessage(err, 'Error al generar las mensualidades')),
  })

  const marcarPagadoMutation = useMutation({
    mutationFn: mensualidadesApi.marcarPagado,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['mensualidades'] })
      toast.success('Marcada como pagada')
    },
    onError: (err) => toast.error(getErrorMessage(err, 'Error al marcar como pagada')),
  })

  const marcarPendienteMutation = useMutation({
    mutationFn: mensualidadesApi.marcarPendiente,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['mensualidades'] })
      toast.success('Deshecho')
    },
    onError: (err) => toast.error(getErrorMessage(err, 'Error al deshacer')),
  })

  const formatMoney = (v: string) => Number(v).toLocaleString('es-CO', { style: 'currency', currency: 'COP' })

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-semibold text-slate-800">Mensualidades</h1>
        <Button
          className="gap-2"
          onClick={() => generarMutation.mutate()}
          disabled={generarMutation.isPending}
          title="Genera todas las mensualidades pendientes de cada alumno desde su ingreso hasta hoy, no solo la del mes actual"
        >
          <RefreshCw size={16} /> Generar mensualidades pendientes
        </Button>
      </div>

      <div className="mb-4 flex flex-wrap items-center gap-3">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={16} />
          <Input
            placeholder="Buscar por nombre..."
            className="w-56 pl-9"
            value={search}
            onChange={(e) => {
              setPage(1)
              setSearch(e.target.value)
            }}
          />
        </div>
        <select
          className="rounded-md border border-slate-300 px-3 py-2 text-sm"
          value={categoriaId}
          onChange={(e) => {
            setPage(1)
            setCategoriaId(e.target.value)
          }}
        >
          <option value="">Todas las categorías</option>
          {categorias?.items.map((c) => (
            <option key={c.id} value={c.id}>
              {c.nombre}
            </option>
          ))}
        </select>
        <select
          className="rounded-md border border-slate-300 px-3 py-2 text-sm"
          value={estado}
          onChange={(e) => {
            setPage(1)
            setEstado(e.target.value as EstadoMensualidad | '')
          }}
        >
          <option value="">Todos los estados</option>
          <option value="pendiente">Pendiente</option>
          <option value="parcial">Parcial</option>
          <option value="pagado">Pagado</option>
          <option value="vencido">Vencido</option>
        </select>
        {alumnoId && (
          <button
            className="flex items-center gap-1 rounded-full bg-slate-100 px-3 py-1 text-xs text-slate-600 hover:bg-slate-200"
            onClick={() => setSearchParams({})}
          >
            Filtrado por alumno #{alumnoId} <X size={12} />
          </button>
        )}
      </div>

      {isLoading ? (
        <p className="text-slate-500">Cargando...</p>
      ) : (
        <div className="overflow-x-auto rounded-lg border border-slate-200 bg-white">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-50 text-slate-600">
              <tr>
                <th className="px-4 py-3">Alumno</th>
                <th className="px-4 py-3">Periodo</th>
                <th className="px-4 py-3">Monto</th>
                <th className="px-4 py-3">Vencimiento</th>
                <th className="px-4 py-3">Estado</th>
                <th className="px-4 py-3" />
              </tr>
            </thead>
            <tbody>
              {data?.items.map((m) => (
                <tr key={m.id} className="border-t border-slate-100">
                  <td className="px-4 py-3 text-slate-800">{m.alumno_nombre}</td>
                  <td className="px-4 py-3 text-slate-600">
                    {m.periodo_inicio} - {m.periodo_fin}
                  </td>
                  <td className="px-4 py-3 text-slate-800">
                    {formatMoney(m.monto)}
                    {m.monto_prorrateado && <span className="ml-1 text-xs text-amber-600">(prorrateado)</span>}
                  </td>
                  <td className="px-4 py-3 text-slate-600">{m.fecha_vencimiento}</td>
                  <td className="px-4 py-3">
                    <span className={`rounded-full px-2 py-1 text-xs font-medium ${ESTADO_COLOR[m.estado]}`}>
                      {ESTADO_LABEL[m.estado]}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right">
                    <div className="flex justify-end gap-2">
                      {Number(m.total_pagado) > 0 && (
                        <button
                          onClick={() => setPagosDe(m.id)}
                          className="flex items-center gap-1 text-xs text-slate-500 hover:text-green-700"
                        >
                          <Receipt size={14} /> Recibos
                        </button>
                      )}
                      {m.estado !== 'pagado' && (
                        <>
                          <Button
                            variant="secondary"
                            onClick={() => setPagoModalFor(m)}
                            className="!px-2 !py-1 text-xs"
                          >
                            Registrar pago
                          </Button>
                          <button
                            onClick={() => marcarPagadoMutation.mutate(m.id)}
                            disabled={marcarPagadoMutation.isPending}
                            title="Marcado rápido para meses históricos (sin recibo)"
                            className="flex items-center gap-1 text-xs text-slate-500 hover:text-green-700"
                          >
                            <CheckCircle2 size={14} /> Marcar pagado
                          </button>
                        </>
                      )}
                      {m.estado === 'pagado' && (
                        <button
                          onClick={() => marcarPendienteMutation.mutate(m.id)}
                          disabled={marcarPendienteMutation.isPending}
                          title="Deshacer marcado histórico"
                          className="flex items-center gap-1 text-xs text-slate-400 hover:text-red-600"
                        >
                          <Undo2 size={14} /> Deshacer
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
              {data?.items.length === 0 && (
                <tr>
                  <td colSpan={6} className="px-4 py-6 text-center text-slate-400">
                    No hay mensualidades registradas.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
          {data && <Pagination page={data.page} pages={data.pages} onPageChange={setPage} />}
        </div>
      )}

      {pagoModalFor && (
        <PagoFormModal mensualidad={pagoModalFor} onClose={() => setPagoModalFor(null)} />
      )}

      {pagosDe !== null && (
        <PagosDeMensualidadModal mensualidadId={pagosDe} onClose={() => setPagosDe(null)} />
      )}
    </div>
  )
}

function PagosDeMensualidadModal({ mensualidadId, onClose }: { mensualidadId: number; onClose: () => void }) {
  const { data, isLoading } = useQuery({
    queryKey: ['pagos', mensualidadId],
    queryFn: () => pagosApi.getPagos({ mensualidad_id: mensualidadId, size: 50 }),
  })

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4" onClick={onClose}>
      <div
        className="w-full max-w-md rounded-lg bg-white p-6 shadow-lg"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-slate-800">Pagos registrados</h2>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600">
            <X size={20} />
          </button>
        </div>
        {isLoading ? (
          <p className="text-sm text-slate-500">Cargando...</p>
        ) : (
          <ul className="space-y-2">
            {data?.items.map((p) => (
              <li key={p.id} className="flex items-center justify-between rounded-md border border-slate-100 px-3 py-2 text-sm">
                <span>
                  {p.fecha_pago} — ${Number(p.monto).toLocaleString('es-CO')} ({p.metodo_pago})
                </span>
                {p.recibo_tipo === 'generado' ? (
                  <Link to={`/recibos/${p.id}`} target="_blank" className="text-green-700 hover:underline">
                    Ver recibo
                  </Link>
                ) : p.recibo_path ? (
                  <a
                    href={p.recibo_path}
                    target="_blank"
                    rel="noreferrer"
                    className="text-green-700 hover:underline"
                  >
                    Ver recibo
                  </a>
                ) : (
                  <span className="text-xs text-slate-400">Sin recibo (histórico)</span>
                )}
              </li>
            ))}
            {data?.items.length === 0 && <p className="text-sm text-slate-400">Sin pagos registrados.</p>}
          </ul>
        )}
      </div>
    </div>
  )
}
