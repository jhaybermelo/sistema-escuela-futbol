import { useEffect, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useNavigate, useParams } from 'react-router-dom'
import toast from 'react-hot-toast'
import * as alumnosApi from '../api/alumnos'
import { Button } from '../components/ui/Button'
import { Input } from '../components/ui/Input'
import { getErrorMessage } from '../lib/errors'

interface FormState {
  numero_identificacion: string
  nombres: string
  apellidos: string
  fecha_nacimiento: string
  fecha_ingreso: string
  acudiente_nombre: string
  acudiente_telefono: string
  acudiente_email: string
  categoria_id: string
}

const emptyForm: FormState = {
  numero_identificacion: '',
  nombres: '',
  apellidos: '',
  fecha_nacimiento: '',
  fecha_ingreso: new Date().toISOString().slice(0, 10),
  acudiente_nombre: '',
  acudiente_telefono: '',
  acudiente_email: '',
  categoria_id: '',
}

export default function AlumnoFormPage() {
  const { id } = useParams()
  const isEdit = Boolean(id)
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [form, setForm] = useState<FormState>(emptyForm)

  const { data: alumno } = useQuery({
    queryKey: ['alumno', id],
    queryFn: () => alumnosApi.getAlumno(Number(id)),
    enabled: isEdit,
  })

  useEffect(() => {
    if (alumno) {
      // Poblar el formulario controlado una vez llega el registro (fetch asíncrono, sin alternativa sin efecto).
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setForm({
        numero_identificacion: alumno.numero_identificacion,
        nombres: alumno.nombres,
        apellidos: alumno.apellidos,
        fecha_nacimiento: alumno.fecha_nacimiento,
        fecha_ingreso: alumno.fecha_ingreso,
        acudiente_nombre: alumno.acudiente_nombre,
        acudiente_telefono: alumno.acudiente_telefono,
        acudiente_email: alumno.acudiente_email ?? '',
        categoria_id: String(alumno.categoria_id),
      })
    }
  }, [alumno])

  const saveMutation = useMutation({
    mutationFn: async () => {
      const input = {
        numero_identificacion: form.numero_identificacion,
        nombres: form.nombres,
        apellidos: form.apellidos,
        fecha_nacimiento: form.fecha_nacimiento,
        fecha_ingreso: form.fecha_ingreso,
        acudiente_nombre: form.acudiente_nombre,
        acudiente_telefono: form.acudiente_telefono,
        acudiente_email: form.acudiente_email || null,
      }
      if (isEdit) {
        return alumnosApi.updateAlumno(Number(id), input)
      }
      return alumnosApi.createAlumno(input)
    },
    onSuccess: (result) => {
      queryClient.invalidateQueries({ queryKey: ['alumnos'] })
      toast.success(isEdit ? 'Alumno actualizado' : 'Alumno creado')
      navigate(`/alumnos/${result.id}`)
    },
    onError: (err) => toast.error(getErrorMessage(err, 'Error al guardar el alumno')),
  })

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    saveMutation.mutate()
  }

  return (
    <div className="max-w-2xl">
      <h1 className="mb-6 text-2xl font-semibold text-slate-800">
        {isEdit ? 'Editar alumno' : 'Nuevo alumno'}
      </h1>
      <form onSubmit={handleSubmit} className="space-y-4 rounded-lg border border-slate-200 bg-white p-6">
        <div className="grid grid-cols-2 gap-4">
          <Input
            label="Número de identificación"
            required
            value={form.numero_identificacion}
            onChange={(e) => setForm({ ...form, numero_identificacion: e.target.value })}
          />
          <div className="flex flex-col gap-1">
            <span className="text-sm font-medium text-slate-700">Categoría</span>
            <span className="rounded-md border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-500">
              {isEdit && alumno ? alumno.categoria_nombre : 'Se asigna automáticamente según la fecha de nacimiento'}
            </span>
          </div>
        </div>
        <div className="grid grid-cols-2 gap-4">
          <Input
            label="Nombres"
            required
            value={form.nombres}
            onChange={(e) => setForm({ ...form, nombres: e.target.value })}
          />
          <Input
            label="Apellidos"
            required
            value={form.apellidos}
            onChange={(e) => setForm({ ...form, apellidos: e.target.value })}
          />
        </div>
        <div className="grid grid-cols-2 gap-4">
          <Input
            label="Fecha de nacimiento"
            type="date"
            required
            value={form.fecha_nacimiento}
            onChange={(e) => setForm({ ...form, fecha_nacimiento: e.target.value })}
          />
          <Input
            label="Fecha de ingreso"
            type="date"
            required
            value={form.fecha_ingreso}
            onChange={(e) => setForm({ ...form, fecha_ingreso: e.target.value })}
          />
        </div>
        <div className="grid grid-cols-2 gap-4">
          <Input
            label="Nombre del acudiente"
            required
            value={form.acudiente_nombre}
            onChange={(e) => setForm({ ...form, acudiente_nombre: e.target.value })}
          />
          <Input
            label="Teléfono del acudiente (WhatsApp)"
            required
            value={form.acudiente_telefono}
            onChange={(e) => setForm({ ...form, acudiente_telefono: e.target.value })}
          />
        </div>
        <Input
          label="Email del acudiente (opcional)"
          type="email"
          value={form.acudiente_email}
          onChange={(e) => setForm({ ...form, acudiente_email: e.target.value })}
        />
        <div className="flex justify-end gap-2 pt-2">
          <Button type="button" variant="secondary" onClick={() => navigate(-1)}>
            Cancelar
          </Button>
          <Button type="submit" disabled={saveMutation.isPending}>
            Guardar
          </Button>
        </div>
      </form>
    </div>
  )
}
