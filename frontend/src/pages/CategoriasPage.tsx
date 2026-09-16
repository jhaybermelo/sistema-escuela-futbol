import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { Plus, Pencil } from 'lucide-react'
import * as categoriasApi from '../api/categorias'
import type { Categoria } from '../types'
import { useAuth } from '../context/AuthContext'
import { Button } from '../components/ui/Button'
import { Input } from '../components/ui/Input'
import { Modal } from '../components/ui/Modal'
import { getErrorMessage } from '../lib/errors'

const DIAS = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom']

interface FormState {
  nombre: string
  anio_nacimiento_min: string
  anio_nacimiento_max: string
  dias_entrenamiento: number[]
}

const emptyForm: FormState = {
  nombre: '',
  anio_nacimiento_min: '',
  anio_nacimiento_max: '',
  dias_entrenamiento: [],
}

export default function CategoriasPage() {
  const { user } = useAuth()
  const queryClient = useQueryClient()
  const [editing, setEditing] = useState<Categoria | null>(null)
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState<FormState>(emptyForm)

  const { data, isLoading } = useQuery({
    queryKey: ['categorias'],
    queryFn: () => categoriasApi.getCategorias(),
  })

  const createMutation = useMutation({
    mutationFn: categoriasApi.createCategoria,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['categorias'] })
      toast.success('Categoría creada')
      closeForm()
    },
    onError: (err) => toast.error(getErrorMessage(err, 'Error al crear la categoría')),
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, input }: { id: number; input: categoriasApi.CategoriaInput }) =>
      categoriasApi.updateCategoria(id, input),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['categorias'] })
      toast.success('Categoría actualizada')
      closeForm()
    },
    onError: (err) => toast.error(getErrorMessage(err, 'Error al actualizar la categoría')),
  })

  function openCreate() {
    setEditing(null)
    setForm(emptyForm)
    setShowForm(true)
  }

  function openEdit(categoria: Categoria) {
    setEditing(categoria)
    setForm({
      nombre: categoria.nombre,
      anio_nacimiento_min: String(categoria.anio_nacimiento_min),
      anio_nacimiento_max: String(categoria.anio_nacimiento_max),
      dias_entrenamiento: categoria.dias_entrenamiento,
    })
    setShowForm(true)
  }

  function closeForm() {
    setShowForm(false)
    setEditing(null)
  }

  function toggleDia(dia: number) {
    setForm((f) => ({
      ...f,
      dias_entrenamiento: f.dias_entrenamiento.includes(dia)
        ? f.dias_entrenamiento.filter((d) => d !== dia)
        : [...f.dias_entrenamiento, dia],
    }))
  }

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    const input: categoriasApi.CategoriaInput = {
      nombre: form.nombre,
      anio_nacimiento_min: Number(form.anio_nacimiento_min),
      anio_nacimiento_max: Number(form.anio_nacimiento_max),
      dias_entrenamiento: form.dias_entrenamiento,
    }
    if (editing) {
      updateMutation.mutate({ id: editing.id, input })
    } else {
      createMutation.mutate(input)
    }
  }

  const isAdmin = user?.rol === 'admin'

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-semibold text-slate-800">Categorías</h1>
        {isAdmin && (
          <Button onClick={openCreate} className="gap-2">
            <Plus size={16} /> Nueva categoría
          </Button>
        )}
      </div>

      {isLoading ? (
        <p className="text-slate-500">Cargando...</p>
      ) : (
        <div className="overflow-x-auto rounded-lg border border-slate-200 bg-white">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-50 text-slate-600">
              <tr>
                <th className="px-4 py-3">Nombre</th>
                <th className="px-4 py-3">Años de nacimiento</th>
                <th className="px-4 py-3">Días de entrenamiento</th>
                {isAdmin && <th className="px-4 py-3" />}
              </tr>
            </thead>
            <tbody>
              {data?.items.map((categoria) => (
                <tr key={categoria.id} className="border-t border-slate-100">
                  <td className="px-4 py-3 font-medium text-slate-800">{categoria.nombre}</td>
                  <td className="px-4 py-3 text-slate-600">
                    {categoria.anio_nacimiento_min === categoria.anio_nacimiento_max
                      ? categoria.anio_nacimiento_min
                      : `${categoria.anio_nacimiento_min} - ${categoria.anio_nacimiento_max}`}
                  </td>
                  <td className="px-4 py-3 text-slate-600">
                    {categoria.dias_entrenamiento.map((d) => DIAS[d]).join(', ') || '—'}
                  </td>
                  {isAdmin && (
                    <td className="px-4 py-3 text-right">
                      <button onClick={() => openEdit(categoria)} className="text-slate-400 hover:text-green-700">
                        <Pencil size={16} />
                      </button>
                    </td>
                  )}
                </tr>
              ))}
              {data?.items.length === 0 && (
                <tr>
                  <td colSpan={4} className="px-4 py-6 text-center text-slate-400">
                    No hay categorías registradas.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}

      {showForm && (
        <Modal title={editing ? 'Editar categoría' : 'Nueva categoría'} onClose={closeForm}>
          <form onSubmit={handleSubmit} className="space-y-4">
            <Input
              label="Nombre"
              required
              value={form.nombre}
              onChange={(e) => setForm({ ...form, nombre: e.target.value })}
            />
            <div className="grid grid-cols-2 gap-3">
              <Input
                label="Año nacimiento mínimo"
                type="number"
                required
                value={form.anio_nacimiento_min}
                onChange={(e) => setForm({ ...form, anio_nacimiento_min: e.target.value })}
              />
              <Input
                label="Año nacimiento máximo"
                type="number"
                required
                value={form.anio_nacimiento_max}
                onChange={(e) => setForm({ ...form, anio_nacimiento_max: e.target.value })}
              />
            </div>
            <div>
              <span className="mb-1 block text-sm font-medium text-slate-700">Días de entrenamiento</span>
              <div className="flex flex-wrap gap-2">
                {DIAS.map((dia, idx) => (
                  <button
                    type="button"
                    key={dia}
                    onClick={() => toggleDia(idx)}
                    className={`rounded-md border px-3 py-1 text-sm ${
                      form.dias_entrenamiento.includes(idx)
                        ? 'border-green-600 bg-green-100 text-green-800'
                        : 'border-slate-300 text-slate-600'
                    }`}
                  >
                    {dia}
                  </button>
                ))}
              </div>
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <Button type="button" variant="secondary" onClick={closeForm}>
                Cancelar
              </Button>
              <Button type="submit" disabled={createMutation.isPending || updateMutation.isPending}>
                Guardar
              </Button>
            </div>
          </form>
        </Modal>
      )}
    </div>
  )
}
