import { useEffect, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { History } from 'lucide-react'
import * as configApi from '../api/config'
import * as alumnosApi from '../api/alumnos'
import { Button } from '../components/ui/Button'
import { Input } from '../components/ui/Input'
import { getErrorMessage } from '../lib/errors'

export default function SchoolConfigPage() {
  const queryClient = useQueryClient()
  const { data } = useQuery({ queryKey: ['school-config'], queryFn: configApi.getConfig })

  const [form, setForm] = useState({
    nombre_escuela: '',
    valor_mensualidad: '',
    dia_corte: '',
    dias_recordatorio_previo: '',
    fecha_inicio: '',
  })

  useEffect(() => {
    if (data) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setForm({
        nombre_escuela: data.nombre_escuela,
        valor_mensualidad: data.valor_mensualidad,
        dia_corte: String(data.dia_corte),
        dias_recordatorio_previo: String(data.dias_recordatorio_previo),
        fecha_inicio: data.fecha_inicio ?? '',
      })
    }
  }, [data])

  const mutation = useMutation({
    mutationFn: () =>
      configApi.updateConfig({
        nombre_escuela: form.nombre_escuela,
        valor_mensualidad: Number(form.valor_mensualidad),
        dia_corte: Number(form.dia_corte),
        dias_recordatorio_previo: Number(form.dias_recordatorio_previo),
        fecha_inicio: form.fecha_inicio || null,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['school-config'] })
      toast.success('Configuración guardada')
    },
    onError: (err) => toast.error(getErrorMessage(err, 'Error al guardar la configuración')),
  })

  const historialMutation = useMutation({
    mutationFn: alumnosApi.generarHistorial,
    onSuccess: (result) => {
      queryClient.invalidateQueries({ queryKey: ['mensualidades'] })
      queryClient.invalidateQueries({ queryKey: ['resumen-alumno'] })
      toast.success(
        `${result.mensualidades_generadas} mensualidad(es) histórica(s) generadas para ${result.alumnos_revisados} alumno(s)`,
      )
    },
    onError: (err) => toast.error(getErrorMessage(err, 'Error al generar el histórico')),
  })

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    mutation.mutate()
  }

  return (
    <div className="max-w-lg space-y-6">
      <div>
        <h1 className="mb-6 text-2xl font-semibold text-slate-800">Configuración de la escuela</h1>
        <form onSubmit={handleSubmit} className="space-y-4 rounded-lg border border-slate-200 bg-white p-6">
          <Input
            label="Nombre de la escuela"
            value={form.nombre_escuela}
            onChange={(e) => setForm({ ...form, nombre_escuela: e.target.value })}
          />
          <Input
            label="Valor de la mensualidad"
            type="number"
            min="0"
            step="0.01"
            value={form.valor_mensualidad}
            onChange={(e) => setForm({ ...form, valor_mensualidad: e.target.value })}
          />
          <Input
            label="Día de corte (1-28)"
            type="number"
            min="1"
            max="28"
            value={form.dia_corte}
            onChange={(e) => setForm({ ...form, dia_corte: e.target.value })}
          />
          <Input
            label="Días de anticipación para recordatorio"
            type="number"
            min="0"
            max="30"
            value={form.dias_recordatorio_previo}
            onChange={(e) => setForm({ ...form, dias_recordatorio_previo: e.target.value })}
          />
          <Input
            label="Fecha de inicio de la escuela"
            type="date"
            value={form.fecha_inicio}
            onChange={(e) => setForm({ ...form, fecha_inicio: e.target.value })}
          />
          <p className="text-xs text-slate-400">
            El histórico de mensualidades de cada alumno nunca empieza antes de esta fecha, aunque su
            fecha de ingreso sea anterior. Déjala vacía si no quieres limitar el histórico.
          </p>
          <div className="flex justify-end pt-2">
            <Button type="submit" disabled={mutation.isPending}>
              Guardar
            </Button>
          </div>
        </form>
      </div>

      <div className="rounded-lg border border-slate-200 bg-white p-6">
        <h2 className="mb-2 text-sm font-semibold text-slate-700">Histórico de mensualidades</h2>
        <p className="mb-4 text-sm text-slate-500">
          Genera las mensualidades faltantes de todos los alumnos activos, desde la fecha de inicio de la
          escuela (o su fecha de ingreso) hasta hoy. Útil tras configurar la fecha de inicio por primera
          vez, o para alumnos que ya existían en el sistema.
        </p>
        <Button
          variant="secondary"
          className="gap-2"
          onClick={() => historialMutation.mutate()}
          disabled={historialMutation.isPending}
        >
          <History size={16} /> Generar histórico para todos los alumnos
        </Button>
      </div>
    </div>
  )
}
