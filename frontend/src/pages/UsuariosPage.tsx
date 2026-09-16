import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { Plus, Shield, Ban, CheckCircle2 } from 'lucide-react'
import * as usuariosApi from '../api/usuarios'
import * as categoriasApi from '../api/categorias'
import type { Usuario } from '../api/usuarios'
import { Button } from '../components/ui/Button'
import { Input } from '../components/ui/Input'
import { Modal } from '../components/ui/Modal'
import { getErrorMessage } from '../lib/errors'

export default function UsuariosPage() {
  const queryClient = useQueryClient()
  const [showForm, setShowForm] = useState(false)
  const [categoriasFor, setCategoriasFor] = useState<Usuario | null>(null)

  const { data, isLoading } = useQuery({ queryKey: ['usuarios'], queryFn: () => usuariosApi.getUsuarios() })

  const toggleActivoMutation = useMutation({
    mutationFn: ({ id, activo }: { id: number; activo: boolean }) =>
      usuariosApi.updateUsuario(id, { activo }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['usuarios'] })
      toast.success('Usuario actualizado')
    },
    onError: (err) => toast.error(getErrorMessage(err, 'Error al actualizar el usuario')),
  })

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-semibold text-slate-800">Usuarios</h1>
        <Button onClick={() => setShowForm(true)} className="gap-2">
          <Plus size={16} /> Nuevo usuario
        </Button>
      </div>

      {isLoading ? (
        <p className="text-slate-500">Cargando...</p>
      ) : (
        <div className="overflow-x-auto rounded-lg border border-slate-200 bg-white">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-50 text-slate-600">
              <tr>
                <th className="px-4 py-3">Nombre</th>
                <th className="px-4 py-3">Email</th>
                <th className="px-4 py-3">Rol</th>
                <th className="px-4 py-3">Categorías</th>
                <th className="px-4 py-3">Estado</th>
                <th className="px-4 py-3" />
              </tr>
            </thead>
            <tbody>
              {data?.items.map((u) => (
                <tr key={u.id} className="border-t border-slate-100">
                  <td className="px-4 py-3 text-slate-800">{u.nombre}</td>
                  <td className="px-4 py-3 text-slate-600">{u.email}</td>
                  <td className="px-4 py-3 text-slate-600 capitalize">{u.rol}</td>
                  <td className="px-4 py-3 text-slate-600">
                    {u.rol === 'entrenador' ? (
                      <button
                        onClick={() => setCategoriasFor(u)}
                        className="flex items-center gap-1 text-green-700 hover:underline"
                      >
                        <Shield size={14} /> {u.categoria_ids.length || 'Asignar'}
                      </button>
                    ) : (
                      '—'
                    )}
                  </td>
                  <td className="px-4 py-3">
                    <span
                      className={`rounded-full px-2 py-1 text-xs font-medium ${
                        u.activo ? 'bg-green-100 text-green-800' : 'bg-slate-100 text-slate-500'
                      }`}
                    >
                      {u.activo ? 'Activo' : 'Inactivo'}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right">
                    <button
                      onClick={() => toggleActivoMutation.mutate({ id: u.id, activo: !u.activo })}
                      className="text-slate-400 hover:text-green-700"
                      title={u.activo ? 'Desactivar' : 'Activar'}
                    >
                      {u.activo ? <Ban size={16} /> : <CheckCircle2 size={16} />}
                    </button>
                  </td>
                </tr>
              ))}
              {data?.items.length === 0 && (
                <tr>
                  <td colSpan={6} className="px-4 py-6 text-center text-slate-400">
                    No hay usuarios registrados.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}

      {showForm && <UsuarioFormModal onClose={() => setShowForm(false)} />}
      {categoriasFor && (
        <CategoriasEntrenadorModal usuario={categoriasFor} onClose={() => setCategoriasFor(null)} />
      )}
    </div>
  )
}

function UsuarioFormModal({ onClose }: { onClose: () => void }) {
  const queryClient = useQueryClient()
  const [email, setEmail] = useState('')
  const [nombre, setNombre] = useState('')
  const [rol, setRol] = useState<'admin' | 'entrenador'>('entrenador')
  const [password, setPassword] = useState('')

  const mutation = useMutation({
    mutationFn: () => usuariosApi.createUsuario({ email, nombre, rol, password }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['usuarios'] })
      toast.success('Usuario creado')
      onClose()
    },
    onError: (err) => toast.error(getErrorMessage(err, 'Error al crear el usuario')),
  })

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    mutation.mutate()
  }

  return (
    <Modal title="Nuevo usuario" onClose={onClose}>
      <form onSubmit={handleSubmit} className="space-y-4">
        <Input label="Nombre" required value={nombre} onChange={(e) => setNombre(e.target.value)} />
        <Input
          label="Email"
          type="email"
          required
          value={email}
          onChange={(e) => setEmail(e.target.value)}
        />
        <div className="flex flex-col gap-1">
          <span className="text-sm font-medium text-slate-700">Rol</span>
          <select
            className="rounded-md border border-slate-300 px-3 py-2 text-sm"
            value={rol}
            onChange={(e) => setRol(e.target.value as 'admin' | 'entrenador')}
          >
            <option value="entrenador">Entrenador</option>
            <option value="admin">Administrador</option>
          </select>
        </div>
        <Input
          label="Contraseña"
          type="password"
          minLength={6}
          required
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />
        <div className="flex justify-end gap-2 pt-2">
          <Button type="button" variant="secondary" onClick={onClose}>
            Cancelar
          </Button>
          <Button type="submit" disabled={mutation.isPending}>
            Crear
          </Button>
        </div>
      </form>
    </Modal>
  )
}

function CategoriasEntrenadorModal({ usuario, onClose }: { usuario: Usuario; onClose: () => void }) {
  const queryClient = useQueryClient()
  const [seleccion, setSeleccion] = useState<number[]>(usuario.categoria_ids)

  const { data: categorias } = useQuery({
    queryKey: ['categorias'],
    queryFn: () => categoriasApi.getCategorias(),
  })

  const mutation = useMutation({
    mutationFn: () => usuariosApi.asignarCategorias(usuario.id, seleccion),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['usuarios'] })
      toast.success('Categorías asignadas')
      onClose()
    },
    onError: (err) => toast.error(getErrorMessage(err, 'Error al asignar categorías')),
  })

  function toggle(id: number) {
    setSeleccion((prev) => (prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]))
  }

  return (
    <Modal title={`Categorías de ${usuario.nombre}`} onClose={onClose}>
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
          Si no se selecciona ninguna categoría, el entrenador podrá ver todos los alumnos (sin datos
          financieros) hasta que se le asigne al menos una.
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
