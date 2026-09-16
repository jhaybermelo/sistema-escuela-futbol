import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import toast from 'react-hot-toast'
import * as pagosApi from '../api/pagos'
import type { Mensualidad } from '../types'
import { Button } from './ui/Button'
import { Input } from './ui/Input'
import { Modal } from './ui/Modal'
import { getErrorMessage } from '../lib/errors'

const METODOS = [
  { value: 'efectivo', label: 'Efectivo' },
  { value: 'transferencia', label: 'Transferencia' },
  { value: 'nequi', label: 'Nequi' },
  { value: 'otro', label: 'Otro' },
]

export function PagoFormModal({
  mensualidad,
  onClose,
}: {
  mensualidad: Mensualidad
  onClose: () => void
}) {
  const queryClient = useQueryClient()
  const navigate = useNavigate()
  const saldoPendiente = Number(mensualidad.monto) - Number(mensualidad.total_pagado)

  const [monto, setMonto] = useState(String(saldoPendiente.toFixed(2)))
  const [fechaPago, setFechaPago] = useState(new Date().toISOString().slice(0, 10))
  const [metodoPago, setMetodoPago] = useState('efectivo')
  const [reciboTipo, setReciboTipo] = useState<'generado' | 'subido'>('generado')
  const [referencia, setReferencia] = useState('')
  const [observaciones, setObservaciones] = useState('')
  const [file, setFile] = useState<File | null>(null)

  const mutation = useMutation({
    mutationFn: () =>
      pagosApi.createPago({
        mensualidad_id: mensualidad.id,
        monto: Number(monto),
        fecha_pago: fechaPago,
        metodo_pago: metodoPago,
        recibo_tipo: reciboTipo,
        referencia: referencia || undefined,
        observaciones: observaciones || undefined,
        file: file ?? undefined,
      }),
    onSuccess: (pago) => {
      queryClient.invalidateQueries({ queryKey: ['mensualidades'] })
      toast.success('Pago registrado')
      onClose()
      if (pago.recibo_tipo === 'generado') {
        navigate(`/recibos/${pago.id}`)
      } else if (pago.recibo_path) {
        window.open(pago.recibo_path, '_blank')
      }
    },
    onError: (err) => toast.error(getErrorMessage(err, 'Error al registrar el pago')),
  })

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (reciboTipo === 'subido' && !file) {
      toast.error('Debes adjuntar el documento del recibo físico')
      return
    }
    mutation.mutate()
  }

  return (
    <Modal title={`Registrar pago — ${mensualidad.alumno_nombre}`} onClose={onClose}>
      <form onSubmit={handleSubmit} className="space-y-4">
        <p className="text-sm text-slate-500">
          Saldo pendiente: <span className="font-semibold text-slate-700">${saldoPendiente.toLocaleString('es-CO')}</span>
        </p>
        <Input
          label="Monto"
          type="number"
          min="0.01"
          step="0.01"
          required
          value={monto}
          onChange={(e) => setMonto(e.target.value)}
        />
        <Input
          label="Fecha de pago"
          type="date"
          required
          value={fechaPago}
          onChange={(e) => setFechaPago(e.target.value)}
        />
        <div className="flex flex-col gap-1">
          <span className="text-sm font-medium text-slate-700">Método de pago</span>
          <select
            className="rounded-md border border-slate-300 px-3 py-2 text-sm"
            value={metodoPago}
            onChange={(e) => setMetodoPago(e.target.value)}
          >
            {METODOS.map((m) => (
              <option key={m.value} value={m.value}>
                {m.label}
              </option>
            ))}
          </select>
        </div>
        <Input
          label="Referencia (opcional)"
          placeholder="Ej. número de transacción"
          value={referencia}
          onChange={(e) => setReferencia(e.target.value)}
        />
        <div className="flex flex-col gap-1">
          <span className="text-sm font-medium text-slate-700">Observaciones (opcional)</span>
          <textarea
            className="rounded-md border border-slate-300 px-3 py-2 text-sm"
            rows={2}
            value={observaciones}
            onChange={(e) => setObservaciones(e.target.value)}
          />
        </div>
        <div className="flex flex-col gap-1">
          <span className="text-sm font-medium text-slate-700">Recibo</span>
          <div className="flex gap-4 text-sm">
            <label className="flex items-center gap-1">
              <input
                type="radio"
                checked={reciboTipo === 'generado'}
                onChange={() => setReciboTipo('generado')}
              />
              Generar recibo oficial
            </label>
            <label className="flex items-center gap-1">
              <input
                type="radio"
                checked={reciboTipo === 'subido'}
                onChange={() => setReciboTipo('subido')}
              />
              Subir recibo físico
            </label>
          </div>
        </div>
        {reciboTipo === 'subido' && (
          <input
            type="file"
            accept="image/*,application/pdf"
            onChange={(e) => setFile(e.target.files?.[0] ?? null)}
            className="text-sm"
          />
        )}
        <div className="flex justify-end gap-2 pt-2">
          <Button type="button" variant="secondary" onClick={onClose}>
            Cancelar
          </Button>
          <Button type="submit" disabled={mutation.isPending}>
            Registrar pago
          </Button>
        </div>
      </form>
    </Modal>
  )
}
