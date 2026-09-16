import { useRef } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link, useParams } from 'react-router-dom'
import toast from 'react-hot-toast'
import { Pencil, Upload, IdCard } from 'lucide-react'
import * as alumnosApi from '../api/alumnos'
import * as mensualidadesApi from '../api/mensualidades'
import { useAuth } from '../context/AuthContext'
import { Button } from '../components/ui/Button'
import { getErrorMessage } from '../lib/errors'

export default function AlumnoDetailPage() {
  const { id } = useParams()
  const { user } = useAuth()
  const queryClient = useQueryClient()
  const fileInputRef = useRef<HTMLInputElement>(null)

  const { data: alumno, isLoading } = useQuery({
    queryKey: ['alumno', id],
    queryFn: () => alumnosApi.getAlumno(Number(id)),
  })

  const { data: resumen } = useQuery({
    queryKey: ['resumen-alumno', id],
    queryFn: () => mensualidadesApi.getResumenAlumno(Number(id)),
    enabled: user?.rol === 'admin',
  })

  const uploadMutation = useMutation({
    mutationFn: (file: File) => alumnosApi.uploadFoto(Number(id), file),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['alumno', id] })
      toast.success('Foto actualizada')
    },
    onError: (err) => toast.error(getErrorMessage(err, 'Error al subir la foto')),
  })

  if (isLoading || !alumno) {
    return <p className="text-slate-500">Cargando...</p>
  }

  const isAdmin = user?.rol === 'admin'

  return (
    <div className="max-w-3xl">
      <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-2xl font-semibold text-slate-800">
          {alumno.nombres} {alumno.apellidos}
        </h1>
        <div className="flex flex-wrap gap-2">
          <Link to={`/alumnos/${alumno.id}/carnet`}>
            <Button variant="secondary" className="gap-2">
              <IdCard size={16} /> Ver carnet
            </Button>
          </Link>
          <Link to={`/alumnos/${alumno.id}/editar`}>
            <Button variant="secondary" className="gap-2">
              <Pencil size={16} /> Editar
            </Button>
          </Link>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
        <div className="col-span-1 max-w-xs md:max-w-none">
          <div className="aspect-square overflow-hidden rounded-lg border border-slate-200 bg-slate-50">
            {alumno.foto_path ? (
              <img src={alumno.foto_path} alt="Foto del alumno" className="h-full w-full object-cover" />
            ) : (
              <div className="flex h-full items-center justify-center text-slate-400">Sin foto</div>
            )}
          </div>
          <input
            ref={fileInputRef}
            type="file"
            accept="image/*"
            className="hidden"
            onChange={(e) => {
              const file = e.target.files?.[0]
              if (file) uploadMutation.mutate(file)
            }}
          />
          <Button
            variant="secondary"
            className="mt-2 w-full gap-2"
            onClick={() => fileInputRef.current?.click()}
            disabled={uploadMutation.isPending}
          >
            <Upload size={16} /> Subir foto
          </Button>
        </div>

        <div className="col-span-2 space-y-4">
          <div className="rounded-lg border border-slate-200 bg-white p-4">
            <h2 className="mb-3 text-sm font-semibold text-slate-500">Datos generales</h2>
            <dl className="grid grid-cols-2 gap-y-2 text-sm">
              <dt className="text-slate-500">Identificación</dt>
              <dd className="text-slate-800">{alumno.numero_identificacion}</dd>
              <dt className="text-slate-500">Categoría</dt>
              <dd className="text-slate-800">
                {alumno.categoria_nombre}
                {alumno.categoria_override && (
                  <span className="ml-2 text-xs text-amber-600">(asignación manual)</span>
                )}
              </dd>
              <dt className="text-slate-500">Fecha de nacimiento</dt>
              <dd className="text-slate-800">{alumno.fecha_nacimiento}</dd>
              <dt className="text-slate-500">Fecha de ingreso</dt>
              <dd className="text-slate-800">{alumno.fecha_ingreso}</dd>
              <dt className="text-slate-500">Estado</dt>
              <dd className="text-slate-800">{alumno.estado}</dd>
            </dl>
          </div>

          <div className="rounded-lg border border-slate-200 bg-white p-4">
            <h2 className="mb-3 text-sm font-semibold text-slate-500">Acudiente</h2>
            <dl className="grid grid-cols-2 gap-y-2 text-sm">
              <dt className="text-slate-500">Nombre</dt>
              <dd className="text-slate-800">{alumno.acudiente_nombre}</dd>
              <dt className="text-slate-500">Teléfono</dt>
              <dd className="text-slate-800">{alumno.acudiente_telefono}</dd>
              <dt className="text-slate-500">Email</dt>
              <dd className="text-slate-800">{alumno.acudiente_email ?? '—'}</dd>
            </dl>
          </div>

          {isAdmin && resumen && (
            <div className="rounded-lg border border-slate-200 bg-white p-4">
              <div className="mb-3 flex items-center justify-between">
                <h2 className="text-sm font-semibold text-slate-500">Mensualidades</h2>
                <Link
                  to={`/mensualidades?alumno_id=${alumno.id}`}
                  className="text-xs text-green-700 hover:underline"
                >
                  Ver detalle
                </Link>
              </div>
              <div className="grid grid-cols-2 gap-3 text-center text-sm sm:grid-cols-4">
                <div>
                  <div className="text-lg font-semibold text-slate-800">{resumen.total_mensualidades}</div>
                  <div className="text-xs text-slate-500">Total</div>
                </div>
                <div>
                  <div className="text-lg font-semibold text-green-700">{resumen.pagadas}</div>
                  <div className="text-xs text-slate-500">Pagadas</div>
                </div>
                <div>
                  <div className="text-lg font-semibold text-amber-600">{resumen.pendientes}</div>
                  <div className="text-xs text-slate-500">Pendientes</div>
                </div>
                <div>
                  <div className="text-lg font-semibold text-red-600">{resumen.vencidas}</div>
                  <div className="text-xs text-slate-500">Vencidas</div>
                </div>
              </div>
              {resumen.meses_desde_inicio_escuela !== null && (
                <p className="mt-3 border-t border-slate-100 pt-3 text-xs text-slate-500">
                  Han pasado <span className="font-medium text-slate-700">{resumen.meses_desde_inicio_escuela}</span>{' '}
                  mensualidades desde que la escuela inició, de las cuales este alumno tiene{' '}
                  <span className="font-medium text-slate-700">{resumen.total_mensualidades}</span> (según su
                  fecha de ingreso).
                </p>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
