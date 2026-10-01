import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { Plus, Shield, Ban, CheckCircle2, Pencil } from 'lucide-react'
import * as profesoresApi from '../api/profesores'
import * as categoriasApi from '../api/categorias'
import type { Profesor } from '../api/profesores'
import { Button } from '../components/ui/Button'
import { Input } from '../components/ui/Input'
import { Modal } from '../components/ui/Modal'
import { getErrorMessage } from '../lib/errors'

export default function ProfesoresPage() {
  const queryClient = useQueryClient()
  const [showForm, setShowForm] = useState(false)
  const [editing, setEditing] = useState<Profesor | null>(null)
  const [categoriasFor, setCategoriasFor] = useState<Profesor | null>(null)

  const { data, isLoading } = useQuery({
    queryKey: ['profesores'],
    queryFn: () => profesoresApi.getProfesores(),
  })

  const toggleActivoMutation = useMutation({
    mutationFn: ({ id, activo }: { id: number; activo: boolean }) =>
      profesoresApi.updateProfesor(id, { activo }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['profesores'] })
      toast.success('Profesor actualizado')
    },
    onError: (err) => toast.error(getErrorMessage(err, 'Error al actualizar el profesor')),
  })

  return (
    <div>
      <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold text-slate-800">Profesores</h1>
          <p className="mt-1 text-sm text-slate-500">
            No tienen acceso al sistema — solo reciben por WhatsApp el aviso cuando un alumno de su
            categoría no ha pagado y no debe ser recibido en el entrenamiento.
          </p>
        </div>
        <Button onClick={() => setShowForm(true)} className="gap-2">
          <Plus size={16} /> Nuevo profesor
        </Button>
      </div>

      {isLoading ? (
        <p className="text-slate-500">Cargando...</p>
      ) : (
        <div className="overflow-x-auto rounded-lg border border-slate-200 bg-white">
          <table className="responsive-table w-full text-left text-sm">
            <thead className="bg-slate-50 text-slate-600">
              <tr>
                <th className="px-4 py-3">Nombre</th>
                <th className="px-4 py-3">Teléfono</th>
                <th className="px-4 py-3">Categorías</th>
                <th className="px-4 py-3">Estado</th>
                <th className="px-4 py-3" />
              </tr>
            </thead>
            <tbody>
              {data?.items.map((p) => (
                <tr key={p.id} className="border-t border-slate-100">
                  <td className="px-4 py-3 text-slate-800" data-label="Nombre">{p.nombre}</td>
                  <td className="px-4 py-3 text-slate-600" data-label="Teléfono">{p.telefono}</td>
                  <td className="px-4 py-3 text-slate-600" data-label="Categorías">
                    <button
                      onClick={() => setCategoriasFor(p)}
                      className="flex items-center gap-1 text-green-700 hover:underline"
                    >
                      <Shield size={14} /> {p.categoria_ids.length || 'Asignar'}
                    </button>
                  </td>
                  <td className="px-4 py-3" data-label="Estado">
                    <span
                      className={`rounded-full px-2 py-1 text-xs font-medium ${
                        p.activo ? 'bg-green-100 text-green-800' : 'bg-slate-100 text-slate-500'
                      }`}
                    >
                      {p.activo ? 'Activo' : 'Inactivo'}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right" data-label="Acciones">
                    <div className="flex items-center justify-end gap-2">
                      <button
                        onClick={() => setEditing(p)}
                        className="text-slate-400 hover:text-green-700"
                        title="Editar"
                      >
                        <Pencil size={16} />
                      </button>
                      <button
                        onClick={() => toggleActivoMutation.mutate({ id: p.id, activo: !p.activo })}
                        className="text-slate-400 hover:text-green-700"
                        title={p.activo ? 'Desactivar' : 'Activar'}
                      >
                        {p.activo ? <Ban size={16} /> : <CheckCircle2 size={16} />}
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
              {data?.items.length === 0 && (
                <tr>
                  <td colSpan={5} className="px-4 py-6 text-center text-slate-400">
                    No hay profesores registrados.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}

      {showForm && <ProfesorFormModal onClose={() => setShowForm(false)} />}
      {editing && <ProfesorFormModal profesor={editing} onClose={() => setEditing(null)} />}
      {categoriasFor && (
        <CategoriasProfesorModal profesor={categoriasFor} onClose={() => setCategoriasFor(null)} />
      )}
    </div>
  )
}

function ProfesorFormModal({ profesor, onClose }: { profesor?: Profesor; onClose: () => void }) {
  const queryClient = useQueryClient()
  const esEdicion = !!profesor
  const [nombre, setNombre] = useState(profesor?.nombre ?? '')
  const [telefono, setTelefono] = useState(profesor?.telefono ?? '')

  const mutation = useMutation({
    mutationFn: () =>
      esEdicion
        ? profesoresApi.updateProfesor(profesor!.id, { nombre, telefono })
        : profesoresApi.createProfesor({ nombre, telefono }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['profesores'] })
      toast.success(esEdicion ? 'Profesor actualizado' : 'Profesor creado')
      onClose()
    },
    onError: (err) => toast.error(getErrorMessage(err, `Error al ${esEdicion ? 'actualizar' : 'crear'} el profesor`)),
  })

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    mutation.mutate()
  }

  return (
    <Modal title={esEdicion ? `Editar ${profesor!.nombre}` : 'Nuevo profesor'} onClose={onClose}>
      <form onSubmit={handleSubmit} className="space-y-4">
        <Input label="Nombre" required value={nombre} onChange={(e) => setNombre(e.target.value)} />
        <Input
          label="Teléfono (WhatsApp)"
          required
          value={telefono}
          onChange={(e) => setTelefono(e.target.value)}
        />
        <div className="flex justify-end gap-2 pt-2">
          <Button type="button" variant="secondary" onClick={onClose}>
            Cancelar
          </Button>
          <Button type="submit" disabled={mutation.isPending}>
            {esEdicion ? 'Guardar' : 'Crear'}
          </Button>
        </div>
      </form>
    </Modal>
  )
}

function CategoriasProfesorModal({ profesor, onClose }: { profesor: Profesor; onClose: () => void }) {
  const queryClient = useQueryClient()
  const [seleccion, setSeleccion] = useState<number[]>(profesor.categoria_ids)

  const { data: categorias } = useQuery({
    queryKey: ['categorias'],
    queryFn: () => categoriasApi.getCategorias(),
  })

  const mutation = useMutation({
    mutationFn: () => profesoresApi.asignarCategorias(profesor.id, seleccion),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['profesores'] })
      toast.success('Categorías asignadas')
      onClose()
    },
    onError: (err) => toast.error(getErrorMessage(err, 'Error al asignar categorías')),
  })

  function toggle(id: number) {
    setSeleccion((prev) => (prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]))
  }

  return (
    <Modal title={`Categorías de ${profesor.nombre}`} onClose={onClose}>
      <div className="space-y-2">
        {categorias?.items.map((c) => (
          <label key={c.id} className="flex items-center gap-2 text-sm">
            <input type="checkbox" checked={seleccion.includes(c.id)} onChange={() => toggle(c.id)} />
            {c.nombre}
          </label>
        ))}
        {categorias?.items.length === 0 && (
          <p className="text-sm text-slate-400">No hay categorías configuradas.</p>
        )}
        <p className="pt-2 text-xs text-slate-400">
          Cuando un alumno de alguna de estas categorías llegue al límite de meses de gracia sin pagar
          (configurable en Configuración), este profesor recibirá un WhatsApp avisando que no debe
          recibirlo en el entrenamiento.
        </p>
      </div>
      <div className="flex justify-end gap-2 pt-4">
        <Button type="button" variant="secondary" onClick={onClose}>
          Cancelar
        </Button>
        <Button onClick={() => mutation.mutate()} disabled={mutation.isPending}>
          Guardar
        </Button>
      </div>
    </Modal>
  )
}
