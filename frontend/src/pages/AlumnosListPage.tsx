import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import toast from 'react-hot-toast'
import { Plus, Search, RefreshCw, Pencil } from 'lucide-react'
import * as alumnosApi from '../api/alumnos'
import * as categoriasApi from '../api/categorias'
import * as mensualidadesApi from '../api/mensualidades'
import { useAuth } from '../context/AuthContext'
import { Button } from '../components/ui/Button'
import { Input } from '../components/ui/Input'
import { Pagination } from '../components/ui/Pagination'
import { getErrorMessage } from '../lib/errors'

const ESTADO_LABEL: Record<string, string> = {
  activo: 'Activo',
  inactivo: 'Inactivo',
  retirado: 'Retirado',
}

const ESTADO_COLOR: Record<string, string> = {
  activo: 'bg-green-100 text-green-800',
  inactivo: 'bg-slate-100 text-slate-600',
  retirado: 'bg-red-100 text-red-700',
}

export default function AlumnosListPage() {
  const { user } = useAuth()
  const queryClient = useQueryClient()
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [categoriaId, setCategoriaId] = useState<string>('')

  const { data, isLoading } = useQuery({
    queryKey: ['alumnos', page, search, categoriaId],
    queryFn: () =>
      alumnosApi.getAlumnos({
        page,
        size: 20,
        search: search || undefined,
        categoria_id: categoriaId ? Number(categoriaId) : undefined,
      }),
  })

  const { data: categorias } = useQuery({
    queryKey: ['categorias'],
    queryFn: () => categoriasApi.getCategorias(),
  })

  const isAdmin = user?.rol === 'admin'

  const { data: cartera } = useQuery({
    queryKey: ['resumen-cartera'],
    queryFn: mensualidadesApi.getResumenCartera,
    enabled: isAdmin,
  })

  const recomputeMutation = useMutation({
    mutationFn: alumnosApi.recomputeCategorias,
    onSuccess: (result) => {
      queryClient.invalidateQueries({ queryKey: ['alumnos'] })
      toast.success(`${result.actualizados.length} alumno(s) actualizados de ${result.total_revisados} revisados`)
    },
    onError: (err) => toast.error(getErrorMessage(err, 'Error al recalcular categorías')),
  })

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-semibold text-slate-800">Alumnos</h1>
        <div className="flex gap-2">
          {isAdmin && (
            <Button
              variant="secondary"
              className="gap-2"
              onClick={() => recomputeMutation.mutate()}
              disabled={recomputeMutation.isPending}
            >
              <RefreshCw size={16} /> Recalcular categorías
            </Button>
          )}
          <Link to="/alumnos/nuevo">
            <Button className="gap-2">
              <Plus size={16} /> Nuevo alumno
            </Button>
          </Link>
        </div>
      </div>

      <div className="mb-4 flex gap-3">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={16} />
          <Input
            placeholder="Buscar por nombre o identificación..."
            className="pl-9"
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
      </div>

      {isLoading ? (
        <p className="text-slate-500">Cargando...</p>
      ) : (
        <div className="overflow-x-auto rounded-lg border border-slate-200 bg-white">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-50 text-slate-600">
              <tr>
                <th className="px-4 py-3">Identificación</th>
                <th className="px-4 py-3">Nombre</th>
                <th className="px-4 py-3">Categoría</th>
                <th className="px-4 py-3">Estado</th>
                {isAdmin && <th className="px-4 py-3">Cartera</th>}
                <th className="px-4 py-3" />
              </tr>
            </thead>
            <tbody>
              {data?.items.map((alumno) => {
                const conteo = cartera?.[alumno.id]
                return (
                  <tr key={alumno.id} className="border-t border-slate-100 hover:bg-slate-50">
                    <td className="px-4 py-3">
                      <Link to={`/alumnos/${alumno.id}`} className="text-green-700 hover:underline">
                        {alumno.numero_identificacion}
                      </Link>
                    </td>
                    <td className="px-4 py-3 text-slate-800">
                      {alumno.nombres} {alumno.apellidos}
                    </td>
                    <td className="px-4 py-3 text-slate-600">{alumno.categoria_nombre}</td>
                    <td className="px-4 py-3">
                      <span className={`rounded-full px-2 py-1 text-xs font-medium ${ESTADO_COLOR[alumno.estado]}`}>
                        {ESTADO_LABEL[alumno.estado]}
                      </span>
                    </td>
                    {isAdmin && (
                      <td className="px-4 py-3">
                        <Link to={`/mensualidades?alumno_id=${alumno.id}`}>
                          {!conteo || (conteo.pendientes === 0 && conteo.vencidas === 0) ? (
                            <span className="rounded-full bg-green-100 px-2 py-1 text-xs font-medium text-green-800">
                              Al día
                            </span>
                          ) : (
                            <span className="flex flex-wrap gap-1">
                              {conteo.vencidas > 0 && (
                                <span className="rounded-full bg-red-100 px-2 py-1 text-xs font-medium text-red-700">
                                  {conteo.vencidas} vencida{conteo.vencidas > 1 ? 's' : ''}
                                </span>
                              )}
                              {conteo.pendientes > 0 && (
                                <span className="rounded-full bg-amber-100 px-2 py-1 text-xs font-medium text-amber-800">
                                  {conteo.pendientes} pendiente{conteo.pendientes > 1 ? 's' : ''}
                                </span>
                              )}
                            </span>
                          )}
                        </Link>
                      </td>
                    )}
                    <td className="px-4 py-3 text-right">
                      <Link
                        to={`/alumnos/${alumno.id}/editar`}
                        className="inline-flex items-center gap-1 text-xs text-slate-500 hover:text-green-700"
                      >
                        <Pencil size={14} /> Editar
                      </Link>
                    </td>
                  </tr>
                )
              })}
              {data?.items.length === 0 && (
                <tr>
                  <td colSpan={isAdmin ? 6 : 5} className="px-4 py-6 text-center text-slate-400">
                    No hay alumnos registrados.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
          {data && <Pagination page={data.page} pages={data.pages} onPageChange={setPage} />}
        </div>
      )}
    </div>
  )
}
