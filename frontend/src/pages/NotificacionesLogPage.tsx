import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { Send, Check, X } from 'lucide-react'
import * as notificacionesApi from '../api/notificaciones'
import { Button } from '../components/ui/Button'
import { Pagination } from '../components/ui/Pagination'
import { getErrorMessage } from '../lib/errors'

const TIPO_LABEL: Record<string, string> = {
  previo_vencimiento: 'Próximo a vencer',
  vencido: 'Vencido',
}

const CANAL_LABEL: Record<string, string> = {
  email: 'Email',
  whatsapp: 'WhatsApp',
}

export default function NotificacionesLogPage() {
  const queryClient = useQueryClient()
  const [page, setPage] = useState(1)

  const { data, isLoading } = useQuery({
    queryKey: ['notificaciones', page],
    queryFn: () => notificacionesApi.getNotificaciones({ page, size: 30 }),
  })

  const enviarMutation = useMutation({
    mutationFn: notificacionesApi.enviarRecordatorios,
    onSuccess: (result) => {
      queryClient.invalidateQueries({ queryKey: ['notificaciones'] })
      toast.success(
        `${result.revisadas} revisadas, ${result.enviados} enviados, ${result.fallidos} fallidos`,
      )
    },
    onError: (err) => toast.error(getErrorMessage(err, 'Error al enviar recordatorios')),
  })

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-semibold text-slate-800">Notificaciones</h1>
        <Button className="gap-2" onClick={() => enviarMutation.mutate()} disabled={enviarMutation.isPending}>
          <Send size={16} /> Enviar recordatorios ahora
        </Button>
      </div>

      {isLoading ? (
        <p className="text-slate-500">Cargando...</p>
      ) : (
        <div className="overflow-x-auto rounded-lg border border-slate-200 bg-white">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-50 text-slate-600">
              <tr>
                <th className="px-4 py-3">Fecha</th>
                <th className="px-4 py-3">Alumno</th>
                <th className="px-4 py-3">Tipo</th>
                <th className="px-4 py-3">Canal</th>
                <th className="px-4 py-3">Resultado</th>
              </tr>
            </thead>
            <tbody>
              {data?.items.map((n) => (
                <tr key={n.id} className="border-t border-slate-100">
                  <td className="px-4 py-3 text-slate-600">{new Date(n.enviado_en).toLocaleString('es-CO')}</td>
                  <td className="px-4 py-3 text-slate-800">{n.alumno_nombre}</td>
                  <td className="px-4 py-3 text-slate-600">{TIPO_LABEL[n.tipo] ?? n.tipo}</td>
                  <td className="px-4 py-3 text-slate-600">{CANAL_LABEL[n.canal] ?? n.canal}</td>
                  <td className="px-4 py-3">
                    {n.exitoso ? (
                      <span className="flex items-center gap-1 text-green-700">
                        <Check size={14} /> Enviado
                      </span>
                    ) : (
                      <span className="flex items-center gap-1 text-red-600" title={n.detalle_error ?? ''}>
                        <X size={14} /> Falló
                      </span>
                    )}
                  </td>
                </tr>
              ))}
              {data?.items.length === 0 && (
                <tr>
                  <td colSpan={5} className="px-4 py-6 text-center text-slate-400">
                    No hay notificaciones registradas.
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
